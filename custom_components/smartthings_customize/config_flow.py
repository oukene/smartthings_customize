"""Config flow to configure SmartThings Customize."""

from collections.abc import Mapping
import logging
from typing import Any

from pysmartthings import SmartThings

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2FlowHandler
from homeassistant.core import callback

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LOCATION_ID,
    CONF_INSTALLED_APP_ID,
    DOMAIN,
    OLD_DATA,
    REQUESTED_SCOPES,
    SCOPES,
    CONF_RESETTING_ENTITIES,
    CONF_ENABLE_SYNTAX_PROPERTY,
)

_LOGGER = logging.getLogger(__name__)


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
        """Check we have the cloud integration set up."""
        if "cloud" not in self.hass.config.components:
            return self.async_abort(
                reason="cloud_not_enabled",
                description_placeholders={"default_config": "default_config"},
            )
        return await super().async_step_user(user_input)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for SmartThings Customize."""
        if not set(data[CONF_TOKEN]["scope"].split()) >= set(SCOPES):
            return self.async_abort(reason="missing_scopes")
        
        client = SmartThings(session=async_get_clientsession(self.hass))
        client.authenticate(data[CONF_TOKEN][CONF_ACCESS_TOKEN])
        locations = await client.get_locations()
        location = locations[0]
        
        # We pick to use the location id as unique id rather than the installed app id
        # as the installed app id could change with the right settings in the SmartApp
        # or the app used to sign in changed for any reason.
        await self.async_set_unique_id(location.location_id)
        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=location.name,
                data={**data, CONF_LOCATION_ID: location.location_id},
            )

        if (entry := self._get_reauth_entry()) and CONF_TOKEN not in entry.data:
            if entry.data[OLD_DATA][CONF_LOCATION_ID] != location.location_id:
                return self.async_abort(reason="reauth_location_mismatch")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(),
                data_updates={
                    **data,
                    CONF_LOCATION_ID: location.location_id,
                },
                unique_id=location.location_id,
            )
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
            return self.async_show_form(
                step_id="reauth_confirm",
            )
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
        # config_entry is stored automatically by parent class

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
                }
            ),
            errors=errors
        )
