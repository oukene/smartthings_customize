"""Config flow to configure SmartThings Customize with OAuth2."""

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2FlowHandler,
    async_get_implementations,
)
from homeassistant.core import callback

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .pysmartthings import SmartThings

from .const import (
    CONF_LOCATION_ID,
    DOMAIN,
    CONF_TOKEN,
    CONF_RESETTING_ENTITIES,
    CONF_ENABLE_SYNTAX_PROPERTY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Use original SmartThings domain for OAuth credentials (Nabu Casa)
SMARTTHINGS_DOMAIN = "smartthings"

# OAuth2 scopes required
SCOPES = [
    "r:devices:*",
    "w:devices:*",
    "x:devices:*",
    "r:hubs:*",
    "r:locations:*",
    "w:locations:*",
    "x:locations:*",
    "r:scenes:*",
    "x:scenes:*",
    "r:rules:*",
    "w:rules:*",
    "sse",
]

REQUESTED_SCOPES = [
    *SCOPES,
    "r:installedapps",
    "w:installedapps",
]


class SmartThingsFlowHandler(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle configuration of SmartThings Customize integrations."""

    VERSION = 3
    MINOR_VERSION = 1
    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": " ".join(REQUESTED_SCOPES)}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user step - use original SmartThings OAuth credentials."""
        if "cloud" not in self.hass.config.components:
            return self.async_abort(
                reason="cloud_not_enabled",
                description_placeholders={"default_config": "default_config"},
            )
        
        # Get OAuth implementations from original SmartThings domain
        implementations = await async_get_implementations(self.hass, SMARTTHINGS_DOMAIN)
        
        if not implementations:
            return self.async_abort(reason="no_oauth_implementation")
        
        # Use the first available implementation
        if len(implementations) == 1:
            self.flow_impl = list(implementations.values())[0]
            return await self.async_step_auth()
        
        # If multiple implementations, let user choose
        if user_input is not None and "implementation" in user_input:
            self.flow_impl = implementations[user_input["implementation"]]
            return await self.async_step_auth()
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("implementation"): vol.In(list(implementations.keys()))}
            ),
        )

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for SmartThings Customize."""
        # Verify we have required scopes
        token_scopes = set(data.get(CONF_TOKEN, {}).get("scope", "").split())
        if not token_scopes >= set(SCOPES):
            _LOGGER.warning("Token missing required scopes. Got: %s", token_scopes)
        
        # Get location info
        access_token = data[CONF_TOKEN][CONF_ACCESS_TOKEN]
        api = SmartThings(async_get_clientsession(self.hass), access_token)
        
        try:
            locations = await api.locations()
            if not locations:
                return self.async_abort(reason="no_locations")
            location = locations[0]
        except Exception as err:
            _LOGGER.error("Failed to get locations: %s", err)
            return self.async_abort(reason="cannot_connect")
        
        # Use location_id as unique id
        await self.async_set_unique_id(location.location_id)
        
        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=location.name,
                data={**data, CONF_LOCATION_ID: location.location_id},
            )
        
        # Handle reauth
        self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
        return self.async_update_reload_and_abort(
            self._get_reauth_entry(), data_updates=data
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon migration of old entries."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        pass

    async def async_step_init(self, user_input: dict[str, Any] = None) -> dict[str, Any]:
        """Handle options flow."""
        errors: dict[str, str] = {}
        options = self.config_entry.options

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_SYNTAX_PROPERTY,
                        default=options.get(CONF_ENABLE_SYNTAX_PROPERTY, False)
                    ): cv.boolean,
                    vol.Optional(
                        CONF_RESETTING_ENTITIES,
                        default=options.get(CONF_RESETTING_ENTITIES, False)
                    ): cv.boolean,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                }
            ),
            errors=errors
        )
