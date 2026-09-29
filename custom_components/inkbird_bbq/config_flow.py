"""Config flow for INKBIRD BBQ."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.device_registry import format_mac

from .const import AUTO_DISCOVERY_NAMES, CONF_MODEL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.components.bluetooth import BluetoothServiceInfoBleak


def _model_from_name(name: str | None) -> str | None:
    """Return the supported model for an exact BLE local name."""
    if name is None:
        return None
    return AUTO_DISCOVERY_NAMES.get(name)


class InkbirdBbqConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle an INKBIRD BBQ config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_model: str | None = None

    async def async_step_bluetooth(
        self,
        discovery_info: BluetoothServiceInfoBleak,
    ) -> ConfigFlowResult:
        """Handle automatic Bluetooth discovery."""
        model = _model_from_name(discovery_info.name)
        if model is None:
            return self.async_abort(reason="not_supported")

        address = format_mac(discovery_info.address).upper()
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self._discovered_address = address
        self._discovered_model = model
        self.context["title_placeholders"] = {"name": model}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm an automatically discovered device."""
        assert self._discovered_address is not None
        assert self._discovered_model is not None

        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_model,
                data={
                    CONF_ADDRESS: self._discovered_address,
                    CONF_MODEL: self._discovered_model,
                },
            )

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "model": self._discovered_model,
                "address": self._discovered_address,
            },
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Offer supported devices already seen by Home Assistant."""
        from homeassistant.components.bluetooth import async_discovered_service_info

        discovered: dict[str, tuple[str, str]] = {}

        for info in async_discovered_service_info(self.hass):
            model = _model_from_name(info.name)
            if model is None:
                continue
            address = format_mac(info.address).upper()
            discovered[address] = (model, address)

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            model, formatted_address = discovered[address]
            await self.async_set_unique_id(formatted_address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=model,
                data={
                    CONF_ADDRESS: formatted_address,
                    CONF_MODEL: model,
                },
            )

        if not discovered:
            return self.async_abort(reason="no_devices_found")

        choices = {
            address: f"{model} ({address})"
            for address, (model, _formatted) in discovered.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(choices),
                }
            ),
        )
