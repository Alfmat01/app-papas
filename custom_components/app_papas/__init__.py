from __future__ import annotations

from homeassistant.util import dt as dt_util
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .api import async_setup_api
from .const import (
    DOMAIN, PLATFORMS, SERVICE_RESET_TODAY, SERVICE_GENERATE_SHOPPING,
    SERVICE_COPY_WEEK, SERVICE_ADD_SHOPPING_ITEM, SERVICE_COMPLETE_CHECKLIST,
    SERVICE_NOTIFY_TODAY, SERVICE_SET_MENU_RECIPE, CONF_ADULT_NAME, CONF_CHILDREN, CONF_NOTIFICATIONS,
    CONF_NOTIFY_SERVICE, CHECKLIST_ITEMS,
)
from .defaults import default_shopping
from .frontend import async_setup_frontend
from .storage import AppPapasStore
from .shopping import sync_menu_shopping
from . import sensor as _sensor  # noqa: F401


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    await async_setup_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = AppPapasStore(hass)
    await store.async_load()
    changed, new_shopping = sync_menu_shopping(store)
    if changed:
        store.data["shopping"] = new_shopping
    settings = store.data.setdefault("settings", {})
    merged_config = {**entry.data, **entry.options}
    settings["adult_name"] = merged_config.get(CONF_ADULT_NAME, settings.get("adult_name", "Papá"))
    children = merged_config.get(CONF_CHILDREN, settings.get("children", ["Niñas"]))
    if isinstance(children, str):
        children = [x.strip() for x in children.split(",") if x.strip()] or ["Niñas"]
    settings["children"] = children
    settings["notifications_enabled"] = bool(merged_config.get(CONF_NOTIFICATIONS, False))
    settings["notify_service"] = merged_config.get(CONF_NOTIFY_SERVICE, "")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store
    await store.async_save(notify=False)
    await async_setup_frontend(hass)
    _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RESET_TODAY):
        return

    async def reset_today(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        day_value = call.data.get("date")
        day = day_value.isoformat() if hasattr(day_value, "isoformat") else (day_value or dt_util.now().date().isoformat())
        store.data.setdefault("days", {})[day] = store.day_template()
        await store.async_save()

    async def generate_shopping(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        changed, new_shopping = sync_menu_shopping(store)
        if changed:
            store.data["shopping"] = new_shopping
        await store.async_save()

    async def copy_week(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        source_offset = int(call.data.get("source_offset", 7))
        days = store.data.setdefault("days", {})
        copied: dict[str, Any] = {}
        today = dt_util.now().date()
        for offset in range(7):
            src = today + timedelta(days=offset - source_offset)
            dst = today + timedelta(days=offset)
            if src.isoformat() in days:
                copied[dst.isoformat()] = days[src.isoformat()]
        days.update(copied)
        await store.async_save()

    async def add_shopping_item(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        category = call.data.get("category", "extras")
        name = str(call.data.get("name", "")).strip()
        if not name:
            return
        category = category if category in store.data.get("shopping", {}) else "extras"
        store.data["shopping"][category].append({"id": f"custom_{uuid4().hex}", "name": name, "checked": False, "source": "manual"})
        await store.async_save()

    async def complete_checklist(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        day_value = call.data.get("date")
        day = day_value.isoformat() if hasattr(day_value, "isoformat") else (day_value or dt_util.now().date().isoformat())
        target = store.get_day(day)
        target["checklist"] = {k: True for k, _ in CHECKLIST_ITEMS}
        await store.async_save()

    async def set_menu_recipe(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        day = str(call.data.get("day", "")).strip()
        meal = str(call.data.get("meal", "")).strip()
        recipe_id = str(call.data.get("recipe_id", "")).strip()
        if day not in store.data.get("menu", {}) or meal not in store.data.get("menu", {}).get(day, {}):
            return
        store.data["menu"][day][meal]["recipe_id"] = recipe_id
        await store.async_save()

    async def notify_today(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        merged_config = {}
        for entry in hass.config_entries.async_entries(DOMAIN):
            merged_config = {**entry.data, **entry.options}
            break
        service = call.data.get("notify_service") or merged_config.get(CONF_NOTIFY_SERVICE, "")
        if not service or "." not in service:
            return
        domain, service_name = service.split(".", 1)
        if domain != "notify":
            return
        day = dt_util.now().date().isoformat()
        d = store.get_day(day)
        adult = store.data.get("settings", {}).get("adult_name", "Papá")
        children = ", ".join(store.data.get("settings", {}).get("children", ["Niñas"]))
        score = store.score(day)
        message = call.data.get("message") or (
            f"🍽️ {adult}: {d.get('desayuno') or 'Sin desayuno registrado'} | "
            f"{d.get('almuerzo') or 'Sin almuerzo registrado'} | {d.get('cena') or 'Sin cena registrada'}\n"
            f"✅ Checklist: {score}/8\n👧 {children}"
        )
        await hass.services.async_call(domain, service_name, {"message": message}, blocking=True)

    schemas = {
        SERVICE_RESET_TODAY: vol.Schema({vol.Optional("date"): cv.date}),
        SERVICE_GENERATE_SHOPPING: vol.Schema({}),
        SERVICE_COPY_WEEK: vol.Schema({vol.Optional("source_offset", default=7): vol.Coerce(int)}),
        SERVICE_ADD_SHOPPING_ITEM: vol.Schema({vol.Required("name"): str, vol.Optional("category", default="extras"): str}),
        SERVICE_COMPLETE_CHECKLIST: vol.Schema({vol.Optional("date"): cv.date}),
        SERVICE_NOTIFY_TODAY: vol.Schema({vol.Optional("notify_service"): str, vol.Optional("message"): str}),
        SERVICE_SET_MENU_RECIPE: vol.Schema({vol.Required("day"): str, vol.Required("meal"): str, vol.Required("recipe_id"): str}),
    }
    funcs = {
        SERVICE_RESET_TODAY: reset_today,
        SERVICE_GENERATE_SHOPPING: generate_shopping,
        SERVICE_COPY_WEEK: copy_week,
        SERVICE_ADD_SHOPPING_ITEM: add_shopping_item,
        SERVICE_COMPLETE_CHECKLIST: complete_checklist,
        SERVICE_NOTIFY_TODAY: notify_today,
        SERVICE_SET_MENU_RECIPE: set_menu_recipe,
    }
    for name, fn in funcs.items():
        hass.services.async_register(DOMAIN, name, fn, schema=schemas[name])


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


def _get_store(hass: HomeAssistant) -> AppPapasStore | None:
    return next(iter(hass.data.get(DOMAIN, {}).values()), None)
