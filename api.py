from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import API_URL, DOMAIN
from .defaults import default_data
from .storage import AppPapasStore


def _get_store(hass: HomeAssistant) -> AppPapasStore | None:
    entries = hass.data.get(DOMAIN, {})
    return next(iter(entries.values()), None)


class AppPapasDataView(HomeAssistantView):
    url = f"{API_URL}/data"
    name = "api:app_papas:data"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        return self.json(store.data)

    async def post(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            payload = await request.json()
        except (TypeError, ValueError):
            return self.json_message("JSON inválido", HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("El cuerpo debe ser un objeto", HTTPStatus.BAD_REQUEST)
        store.data = AppPapasStore._merge(default_data(), payload)
        await store.async_save()
        return self.json(store.data)


class AppPapasDayView(HomeAssistantView):
    url = f"{API_URL}/day/{{day}}"
    name = "api:app_papas:day"
    requires_auth = True

    async def get(self, request: web.Request, day: str) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            date.fromisoformat(day)
        except ValueError:
            return self.json_message("Fecha inválida", HTTPStatus.BAD_REQUEST)
        return self.json(store.data.setdefault("days", {}).get(day, {
            "desayuno": "", "almuerzo": "", "cena": "", "notas": "", "checklist": {}
        }))

    async def post(self, request: web.Request, day: str) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        try:
            date.fromisoformat(day)
            payload = await request.json()
        except (TypeError, ValueError):
            return self.json_message("Fecha o JSON inválido", HTTPStatus.BAD_REQUEST)
        if not isinstance(payload, dict):
            return self.json_message("El cuerpo debe ser un objeto", HTTPStatus.BAD_REQUEST)
        store.data.setdefault("days", {})[day] = {
            "desayuno": str(payload.get("desayuno", "")),
            "almuerzo": str(payload.get("almuerzo", "")),
            "cena": str(payload.get("cena", "")),
            "notas": str(payload.get("notas", "")),
            "checklist": payload.get("checklist", {}) if isinstance(payload.get("checklist", {}), dict) else {},
        }
        await store.async_save()
        return self.json(store.data["days"][day])


async def async_setup_api(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_api_registered"):
        return
    hass.http.register_view(AppPapasDataView())
    hass.http.register_view(AppPapasDayView())
    hass.data[f"{DOMAIN}_api_registered"] = True
