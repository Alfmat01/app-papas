from __future__ import annotations

from datetime import date
from http import HTTPStatus
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import API_URL, DOMAIN
from .storage import AppPapasStore
from .shopping import sync_menu_shopping


def _get_store(hass: HomeAssistant) -> AppPapasStore | None:
    return next(iter(hass.data.get(DOMAIN, {}).values()), None)


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
        old_menu = store.data.get("menu")
        store.data = store._merge(store.data, payload)
        if "menu" in payload and payload.get("menu") != old_menu:
            changed, new_shopping = sync_menu_shopping(store)
            if changed:
                store.data["shopping"] = new_shopping
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
        return self.json(store.get_day(day))

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
        current = store.get_day(day)
        for key in ("desayuno", "almuerzo", "cena", "notas"):
            if key in payload:
                current[key] = str(payload.get(key, ""))
        if isinstance(payload.get("checklist"), dict):
            current["checklist"] = {str(k): bool(v) for k, v in payload["checklist"].items()}
        await store.async_save()
        return self.json(current)


class AppPapasStatsView(HomeAssistantView):
    url = f"{API_URL}/stats"
    name = "api:app_papas:stats"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        store = _get_store(request.app["hass"])
        if store is None:
            return self.json_message("Integración no configurada", HTTPStatus.NOT_FOUND)
        today = dt_util.now().date()
        history = store.history(today, 14)
        return self.json({
            "today_score": store.score(today.isoformat()),
            "streak": store.streak(today),
            "history": history,
            "shopping_pending": store.shopping_pending(),
        })


async def async_setup_api(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_api_registered"):
        return
    hass.http.register_view(AppPapasDataView())
    hass.http.register_view(AppPapasDayView())
    hass.http.register_view(AppPapasStatsView())
    hass.data[f"{DOMAIN}_api_registered"] = True
