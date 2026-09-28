"""Config flow for INKBIRD BBQ."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


class InkbirdBbqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an INKBIRD BBQ config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Start manual setup while Bluetooth discovery is implemented."""
        if user_input is not None:
            name = user_input["name"].strip()
            await self.async_set_unique_id(name.lower().replace(" ", "_"))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=name, data={"name": name})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("name", default="INKBIRD BBQ"): str}),
        )
