from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from typing import Any, Callable, Awaitable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION, CHECKLIST_ITEMS
from .defaults import default_data


class AppPapasStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}.json")
        self.data: dict[str, Any] = default_data()
        self._listeners: set[Callable[[], None]] = set()

    async def async_load(self) -> None:
        saved = await self._store.async_load()
        if saved:
            self.data = self._migrate(saved)
        self.data = self._merge(default_data(), self.data)
        self.data["schema_version"] = STORAGE_VERSION
        await self._store.async_save(self.data)

    async def async_save(self, notify: bool = True) -> None:
        self.data["schema_version"] = STORAGE_VERSION
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

    @classmethod
    def _migrate(cls, saved: dict[str, Any]) -> dict[str, Any]:
        data = deepcopy(saved)
        version = int(data.get("schema_version", 1))
        if version < 2:
            data.setdefault("settings", {})
            data["settings"].setdefault("adult_name", "Papá")
            data["settings"].setdefault("children", ["Niñas"])
            data.setdefault("emergency_meals", [])
            data["schema_version"] = 2
        return data

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
