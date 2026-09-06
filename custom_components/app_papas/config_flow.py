from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME

from .const import DOMAIN, DEFAULT_TITLE


class AppPapasConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the setup of Alimentación para Papás."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        """Create the single App Papás config entry."""
        if self.hass.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_NAME: user_input[CONF_NAME]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_NAME, default=DEFAULT_TITLE): str}
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return AppPapasOptionsFlow(config_entry)


class AppPapasOptionsFlow(OptionsFlow):
    """Handle App Papás options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.config_entry.data.get(CONF_NAME, DEFAULT_TITLE)
                    ): str
                }
            ),
        )
