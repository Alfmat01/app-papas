from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_TITLE, DEFAULT_TITLE, DOMAIN


class AppPapasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_TITLE], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TITLE, default=DEFAULT_TITLE): str}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AppPapasOptionsFlow(config_entry)


class AppPapasOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_TITLE, default=self.config_entry.title): str}),
        )
