from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    DOMAIN, DEFAULT_TITLE, DEFAULT_ADULT_NAME, DEFAULT_CHILDREN,
    CONF_ADULT_NAME, CONF_CHILDREN, CONF_NOTIFICATIONS, CONF_NOTIFY_SERVICE,
    CONF_MEALDB_API_KEY, DEFAULT_MEALDB_API_KEY,
)


class AppPapasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self.hass.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_ADULT_NAME: user_input[CONF_ADULT_NAME],
                    CONF_CHILDREN: user_input[CONF_CHILDREN],
                    CONF_NOTIFICATIONS: user_input[CONF_NOTIFICATIONS],
                    CONF_NOTIFY_SERVICE: user_input.get(CONF_NOTIFY_SERVICE, ""),
                    CONF_MEALDB_API_KEY: user_input.get(CONF_MEALDB_API_KEY, DEFAULT_MEALDB_API_KEY) or DEFAULT_MEALDB_API_KEY,
                },
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=DEFAULT_TITLE): str,
                vol.Required(CONF_ADULT_NAME, default=DEFAULT_ADULT_NAME): str,
                vol.Required(CONF_CHILDREN, default=DEFAULT_CHILDREN): str,
                vol.Required(CONF_NOTIFICATIONS, default=False): bool,
                vol.Optional(CONF_NOTIFY_SERVICE, default=""): str,
                vol.Optional(CONF_MEALDB_API_KEY, default=DEFAULT_MEALDB_API_KEY): str,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AppPapasOptionsFlow()


class AppPapasOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = self.config_entry.data
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        children = current.get(CONF_CHILDREN, [DEFAULT_CHILDREN])
        if isinstance(children, list):
            children = ", ".join(str(x) for x in children)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=self.config_entry.title): str,
                vol.Required(CONF_ADULT_NAME, default=current.get(CONF_ADULT_NAME, DEFAULT_ADULT_NAME)): str,
                vol.Required(CONF_CHILDREN, default=children): str,
                vol.Required(CONF_NOTIFICATIONS, default=current.get(CONF_NOTIFICATIONS, False)): bool,
                vol.Optional(CONF_NOTIFY_SERVICE, default=current.get(CONF_NOTIFY_SERVICE, "")): str,
                vol.Optional(CONF_MEALDB_API_KEY, default=current.get(CONF_MEALDB_API_KEY, DEFAULT_MEALDB_API_KEY)): str,
            }),
        )
