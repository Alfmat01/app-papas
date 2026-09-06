from __future__ import annotations

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
    SERVICE_NOTIFY_TODAY, CONF_ADULT_NAME, CONF_CHILDREN, CONF_NOTIFICATIONS,
    CONF_NOTIFY_SERVICE, CHECKLIST_ITEMS,
)
from .defaults import default_shopping
from .frontend import async_setup_frontend
from .storage import AppPapasStore


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    await async_setup_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = AppPapasStore(hass)
    await store.async_load()
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
        day = day_value.isoformat() if hasattr(day_value, "isoformat") else (day_value or hass.config.now().date().isoformat())
        store.data.setdefault("days", {})[day] = store.day_template()
        await store.async_save()

    async def generate_shopping(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        base = default_shopping()
        vocabulary = {
            "proteina": ["huevo", "pollo", "atún", "atun", "carne", "yogur", "yogurt", "pavo", "jamón", "jamon", "salchicha", "proteína", "proteina", "bacon"],
            "carbohidratos": ["arroz", "avena", "pan", "pasta", "macarrón", "macarrones", "patata", "tostada", "pizza", "frijol", "frijoles"],
            "verduras_frutas": ["brócoli", "brocoli", "ensalada", "verdura", "zanahoria", "aguacate", "fruta", "plátano", "platano", "espinaca", "coliflor", "tomate", "maíz", "maiz"],
            "extras": ["queso", "aceite", "salsa", "leche", "nueces", "mantequilla"],
        }
        canonical = {
            "huevo":"Huevos", "pollo":"Pollo", "atún":"Atún", "atun":"Atún", "carne":"Carne picada", "yogur":"Yogur griego", "yogurt":"Yogur griego", "pavo":"Pavo", "jamón":"Jamón", "jamon":"Jamón", "salchicha":"Salchichas", "bacon":"Bacon", "arroz":"Arroz", "avena":"Avena", "pan":"Pan", "pasta":"Pasta", "macarrón":"Macarrones", "macarrones":"Macarrones", "patata":"Patatas", "tostada":"Tostadas", "pizza":"Pizza", "frijol":"Frijoles", "frijoles":"Frijoles", "brócoli":"Brócoli", "brocoli":"Brócoli", "ensalada":"Ensalada", "verdura":"Verduras", "zanahoria":"Zanahorias", "aguacate":"Aguacate", "fruta":"Fruta", "plátano":"Plátanos", "platano":"Plátanos", "espinaca":"Espinacas", "coliflor":"Coliflor", "tomate":"Tomate", "maíz":"Maíz", "maiz":"Maíz", "queso":"Queso", "aceite":"Aceite de oliva", "salsa":"Salsa", "leche":"Leche", "nueces":"Nueces", "mantequilla":"Mantequilla", "proteína":"Proteína", "proteina":"Proteína",
        }
        detected = {k: set() for k in vocabulary}
        for day in store.data.get("menu", {}).values():
            for meal in day.values():
                for text in (meal.get("papa", ""), meal.get("ninas", "")):
                    low = str(text).lower()
                    for category, words in vocabulary.items():
                        for word in words:
                            if word in low:
                                detected[category].add(canonical.get(word, word.title()))
        generated = {category: list(items) for category, items in base.items()}
        idx = 2000
        for category, names in detected.items():
            existing = {item["name"].lower() for item in generated[category]}
            for name in sorted(names):
                if name.lower() in existing:
                    continue
                idx += 1
                generated[category].append({"id": f"menu_{idx}", "name": name, "checked": False, "source": "menu"})
        for category, items in store.data.get("shopping", {}).items():
            for item in items:
                if item.get("source") in ("custom", "manual"):
                    generated.setdefault(category, []).append(item)
        store.data["shopping"] = generated
        await store.async_save()

    async def copy_week(call: ServiceCall) -> None:
        store = _get_store(hass)
        if not store:
            return
        source_offset = int(call.data.get("source_offset", 7))
        days = store.data.setdefault("days", {})
        copied: dict[str, Any] = {}
        today = hass.config.now().date()
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
        day = day_value.isoformat() if hasattr(day_value, "isoformat") else (day_value or hass.config.now().date().isoformat())
        target = store.get_day(day)
        target["checklist"] = {k: True for k, _ in CHECKLIST_ITEMS}
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
        day = hass.config.now().date().isoformat()
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
    }
    funcs = {
        SERVICE_RESET_TODAY: reset_today,
        SERVICE_GENERATE_SHOPPING: generate_shopping,
        SERVICE_COPY_WEEK: copy_week,
        SERVICE_ADD_SHOPPING_ITEM: add_shopping_item,
        SERVICE_COMPLETE_CHECKLIST: complete_checklist,
        SERVICE_NOTIFY_TODAY: notify_today,
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
