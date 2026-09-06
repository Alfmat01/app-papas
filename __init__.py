from __future__ import annotations

from datetime import date

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .api import async_setup_api
from .const import DOMAIN
from .defaults import default_shopping
from .frontend import async_setup_frontend
from .storage import AppPapasStore

PLATFORMS: list[str] = []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    await async_setup_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = AppPapasStore(hass)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store
    await async_setup_frontend(hass)

    if not hass.services.has_service(DOMAIN, "reset_today"):
        async def reset_today(call: ServiceCall) -> None:
            day = call.data.get("date") or date.today().isoformat()
            current = _get_store(hass)
            if current is None:
                return
            current.data.setdefault("days", {})[day] = {
                "desayuno": "", "almuerzo": "", "cena": "", "notas": "", "checklist": {}
            }
            await current.async_save()

        hass.services.async_register(
            DOMAIN,
            "reset_today",
            reset_today,
            schema=vol.Schema({vol.Optional("date"): str}),
        )

    if not hass.services.has_service(DOMAIN, "generate_shopping"):
        async def generate_shopping(call: ServiceCall) -> None:
            current = _get_store(hass)
            if current is None:
                return
            names = {"proteina": set(), "carbohidratos": set(), "verduras_frutas": set(), "extras": set()}
            for day in current.data.get("menu", {}).values():
                for meal in day.values():
                    for text in (meal.get("papa", ""), meal.get("ninas", "")):
                        lower = text.lower()
                        if any(x in lower for x in ("huevo", "pollo", "atún", "atun", "carne", "yogur", "pavo", "jamón", "jamon", "salchicha", "proteína", "proteina")):
                            names["proteina"].add(text)
                        if any(x in lower for x in ("arroz", "avena", "pan", "pasta", "macarrones", "patata", "tostada", "pizza")):
                            names["carbohidratos"].add(text)
                        if any(x in lower for x in ("brócoli", "brocoli", "ensalada", "verdura", "zanahoria", "aguacate", "fruta", "plátano", "platano")):
                            names["verduras_frutas"].add(text)
            base = default_shopping()
            generated_id = 1000
            for category, values in names.items():
                for text in sorted(values):
                    generated_id += 1
                    base[category].append({"id": f"menu_{generated_id}", "name": text, "checked": False, "source": "menu"})
            current.data["shopping"] = base
            await current.async_save()

        hass.services.async_register(DOMAIN, "generate_shopping", generate_shopping)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True


def _get_store(hass: HomeAssistant) -> AppPapasStore | None:
    return next(iter(hass.data.get(DOMAIN, {}).values()), None)
