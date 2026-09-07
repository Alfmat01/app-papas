from __future__ import annotations

from copy import deepcopy
import re
from datetime import date, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, DATA_SCHEMA_VERSION, CHECKLIST_ITEMS
from .defaults import default_data
from .recipes import default_recipes


class AppPapasStorage(Store[dict[str, Any]]):
    """Persistent storage for App Papás.

    The Home Assistant Store version intentionally remains at 1. Schema
    migrations are handled by AppPapasStore.async_load so upgrades cannot
    fail because of a Store major-version migration.
    """


class AppPapasStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = AppPapasStorage(hass, STORAGE_VERSION, f"{STORAGE_KEY}.json")
        self.data: dict[str, Any] = default_data()
        self._listeners: set[Callable[[], None]] = set()

    @staticmethod
    def _migrate_schema(data: dict[str, Any]) -> dict[str, Any]:
        """Migrate the application data schema without changing Store version."""
        data = deepcopy(data)
        data.setdefault("plan", {})
        data.setdefault("menu", {})
        data.setdefault("days", {})
        data.setdefault("shopping", {})
        settings = data.setdefault("settings", {})
        settings.setdefault("theme", "system")
        settings.setdefault("active_tab", "hoy")
        settings.setdefault("adult_name", "Papá")
        settings.setdefault("children", ["Niñas"])
        settings.setdefault("notifications_enabled", False)
        settings.setdefault("notify_service", "")
        settings.setdefault("mealdb_api_key", "1")
        data.setdefault("emergency_meals", [])
        if not isinstance(data.get("recipes"), list) or not data.get("recipes"):
            data["recipes"] = default_recipes()
        data["schema_version"] = DATA_SCHEMA_VERSION
        return data

    async def async_load(self) -> None:
        saved = await self._store.async_load()
        if saved:
            self.data = saved
        self.data = self._merge(default_data(), self.data)
        self.data = self._migrate_schema(self.data)
        self._ensure_recipe_links()
        await self._store.async_save(self.data)


    def _ensure_recipe_links(self) -> None:
        """Associate legacy/free-text menu entries with close matching recipes."""
        recipes = {str(r.get("id")): r for r in self.data.get("recipes", []) if isinstance(r, dict)}
        for meals in self.data.get("menu", {}).values():
            if not isinstance(meals, dict):
                continue
            for meal in meals.values():
                if not isinstance(meal, dict) or meal.get("recipe_id") in recipes:
                    continue
                texts = " ".join(str(meal.get(k, "")) for k in ("papa", "ninas")).casefold()
                if not texts.strip():
                    continue
                matches: list[tuple[int, str]] = []
                for rid, rec in recipes.items():
                    for alias in [str(rec.get("name", "")), *[str(a) for a in rec.get("aliases", [])]]:
                        alias_norm = alias.casefold().strip()
                        if alias_norm and re.search(rf"(?<!\w){re.escape(alias_norm)}(?!\w)", texts):
                            matches.append((len(alias_norm), rid))
                if matches:
                    meal["recipe_id"] = max(matches)[1]

    async def async_save(self, notify: bool = True) -> None:
        self.data["schema_version"] = DATA_SCHEMA_VERSION
        await self._store.async_save(self.data)
        if notify:
            for listener in tuple(self._listeners):
                listener()

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @staticmethod
    def _merge(default: Any, saved: Any) -> Any:
        if isinstance(default, dict) and isinstance(saved, dict):
            merged = deepcopy(default)
            for key, value in saved.items():
                merged[key] = AppPapasStore._merge(merged[key], value) if key in merged else value
            return merged
        return saved

    @staticmethod
    def day_template() -> dict[str, Any]:
        return {"desayuno": "", "almuerzo": "", "cena": "", "notas": "", "checklist": {}}

    def get_day(self, day: str) -> dict[str, Any]:
        days = self.data.setdefault("days", {})
        if day not in days:
            days[day] = self.day_template()
        days[day].setdefault("checklist", {})
        for key in ("desayuno", "almuerzo", "cena", "notas"):
            days[day].setdefault(key, "")
        return days[day]

    @staticmethod
    def score_for_day(day_data: dict[str, Any]) -> int:
        checks = day_data.get("checklist", {})
        return sum(1 for key, _ in CHECKLIST_ITEMS if checks.get(key))

    def score(self, day: str) -> int:
        return self.score_for_day(self.get_day(day))

    def history(self, end: date | None = None, days: int = 7) -> list[dict[str, Any]]:
        end = end or date.today()
        result = []
        for offset in range(days - 1, -1, -1):
            current = end - timedelta(days=offset)
            key = current.isoformat()
            d = self.data.get("days", {}).get(key, self.day_template())
            result.append({"date": key, "score": self.score_for_day(d)})
        return result

    def streak(self, end: date | None = None) -> int:
        current = end or date.today()
        streak = 0
        while True:
            d = self.data.get("days", {}).get(current.isoformat())
            if not d or self.score_for_day(d) == 0:
                break
            streak += 1
            current -= timedelta(days=1)
        return streak

    def shopping_pending(self) -> int:
        return sum(
            1 for items in self.data.get("shopping", {}).values()
            for item in items if not item.get("checked")
        )
