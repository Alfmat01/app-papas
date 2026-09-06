from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .defaults import default_data


class AppPapasStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}.json")
        self.data: dict[str, Any] = default_data()

    async def async_load(self) -> None:
        saved = await self._store.async_load()
        if saved:
            self.data = self._merge(default_data(), saved)

    async def async_save(self) -> None:
        await self._store.async_save(self.data)

    @staticmethod
    def _merge(default: Any, saved: Any) -> Any:
        if isinstance(default, dict) and isinstance(saved, dict):
            merged = deepcopy(default)
            for key, value in saved.items():
                merged[key] = AppPapasStore._merge(merged[key], value) if key in merged else value
            return merged
        return saved
