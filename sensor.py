from __future__ import annotations

from datetime import date

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CHECKLIST_ITEMS
from .storage import AppPapasStore


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data.get("app_papas", {}).get(entry.entry_id)
    if not store:
        return
    async_add_entities([
        AppPapasSensor(store, entry.entry_id, "checklist", "Checklist hoy"),
        AppPapasSensor(store, entry.entry_id, "shopping_pending", "Compra pendiente"),
        AppPapasSensor(store, entry.entry_id, "streak", "Racha actual"),
        AppPapasSensor(store, entry.entry_id, "today_score", "Puntuación de hoy"),
        AppPapasSensor(store, entry.entry_id, "next_meal", "Próxima comida"),
    ])


class AppPapasSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, store: AppPapasStore, entry_id: str, kind: str, name: str) -> None:
        self._store = store
        self._kind = kind
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{kind}"
        self._remove_listener = store.add_listener(self._on_store_update)
        self._value = None
        self._attrs = {}
        self._update()

    @property
    def native_value(self):
        return self._value

    @property
    def extra_state_attributes(self):
        return self._attrs

    def _on_store_update(self) -> None:
        self._update()
        if self.hass:
            self.async_write_ha_state()

    def _update(self) -> None:
        today = self._store.hass.config.now().date().isoformat()
        d = self._store.get_day(today)
        score = self._store.score(today)
        pending = self._store.shopping_pending()
        if self._kind in ("checklist", "today_score"):
            self._value = score
            self._attrs = {
                "total": len(CHECKLIST_ITEMS),
                "completed": score,
                "date": today,
                "progress_percent": round(score / len(CHECKLIST_ITEMS) * 100),
            }
        elif self._kind == "shopping_pending":
            self._value = pending
            self._attrs = {"pending": pending}
        elif self._kind == "streak":
            self._value = self._store.streak(self._store.hass.config.now().date())
            self._attrs = {"days": self._value}
        else:
            if not d.get("desayuno"):
                next_name = "Desayuno"
            elif not d.get("almuerzo"):
                next_name = "Almuerzo"
            elif not d.get("cena"):
                next_name = "Cena"
            else:
                next_name = "Completado"
            self._value = next_name
            self._attrs = {
                "desayuno": d.get("desayuno", ""),
                "almuerzo": d.get("almuerzo", ""),
                "cena": d.get("cena", ""),
                "date": today,
            }

    async def async_will_remove_from_hass(self) -> None:
        self._remove_listener()
