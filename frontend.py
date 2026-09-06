from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME, PANEL_PATH, STATIC_URL

FRONTEND_DIR = Path(__file__).parent / "frontend"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Register the App Papás static assets and sidebar panel once."""
    if hass.data.get(f"{DOMAIN}_frontend_registered"):
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), False)]
    )

    if PANEL_PATH not in hass.data.get("frontend_panels", {}):
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=NAME,
            sidebar_icon="mdi:food-apple",
            frontend_url_path=PANEL_PATH,
            config={
                "_panel_custom": {
                    "name": "app-papas-panel",
                    "module_url": f"{STATIC_URL}/app-papas.js",
                    "embed_iframe": False,
                    "trust_external": False,
                }
            },
            require_admin=False,
        )

    hass.data[f"{DOMAIN}_frontend_registered"] = True
