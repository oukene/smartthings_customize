"""Config flow to configure SmartThings."""

from collections.abc import Mapping
import logging
from typing import Any

from .pysmartthings import SmartThings
from .pysmartthings.installedapp import format_install_url
import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import (
    CONF_APP_ID,
    CONF_INSTALLED_APP_ID,
    CONF_LOCATION_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    VAL_UID_MATCHER,
    #CONF_ENABLE_DEFAULT_ENTITIES,
    CONF_RESETTING_ENTITIES,
    CONF_ENABLE_SYNTAX_PROPERTY,
)
from .smartapp import (
    format_unique_id,
    get_webhook_url,
    setup_smartapp_for_oauth,
    setup_smartapp_endpoint,
    validate_webhook_requirements,
)

_LOGGER = logging.getLogger(__name__)



class SmartThingsFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle configuration of SmartThings integrations."""

    VERSION = 2

    app_id: str
    location_id: str

    def __init__(self) -> None:
        """Create a new instance of the flow handler."""
        self.oauth_client_secret = None
        self.oauth_client_id = None
        self.installed_app_id = None
        self.refresh_token = None
        self.endpoints_initialized = False

    async def async_step_import(self, user_input=None):
        """Occurs when a previously entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate and confirm webhook setup."""
        if not self.endpoints_initialized:
            self.endpoints_initialized = True
            await setup_smartapp_endpoint(
                self.hass, len(self._async_current_entries()) == 0
            )
        webhook_url = get_webhook_url(self.hass)

        # Abort if the webhook is invalid
        if not validate_webhook_requirements(self.hass):
            return self.async_abort(
                reason="invalid_webhook_url",
                description_placeholders={
                    "webhook_url": webhook_url,
                    "component_url": (
                        "https://www.home-assistant.io/integrations/smartthings/"
                    ),
                },
            )

        # Show the confirmation
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                description_placeholders={"webhook_url": webhook_url},
            )

        # Show the next screen
        return await self.async_step_oauth_credentials()

    async def async_step_oauth_credentials(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Collect the OAuth credentials created in the SmartThings Developer Portal."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self._show_step_oauth_credentials(errors)

        app_id = user_input.get(CONF_APP_ID, "").strip()
        client_id = user_input.get(CONF_CLIENT_ID, "").strip()
        client_secret = user_input.get(CONF_CLIENT_SECRET, "").strip()

        # Validate app_id is UUID format
        if not VAL_UID_MATCHER.match(app_id):
            errors[CONF_APP_ID] = "app_id_invalid_format"
            return self._show_step_oauth_credentials(errors)

        self.app_id = app_id
        self.oauth_client_id = client_id
        self.oauth_client_secret = client_secret

        # If an existing entry already uses this app_id, reuse its OAuth credentials
        # so the user does not have to re-enter them for a second location.
        existing = next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.data.get(CONF_APP_ID) == app_id
            ),
            None,
        )
        if existing:
            self.oauth_client_id = existing.data[CONF_CLIENT_ID]
            self.oauth_client_secret = existing.data[CONF_CLIENT_SECRET]

        # Store app_id in flow context so the webhook callback can locate this flow.
        self.context["app_id"] = app_id

        # Register the SmartApp with the webhook manager so incoming lifecycle
        # events (INSTALL, PING, etc.) can be dispatched.  The public key is not
        # yet available because we have no access token; signature verification
        # will be enabled once async_setup_entry fetches the full app info.
        setup_smartapp_for_oauth(self.hass, app_id)

        return await self.async_step_authorize()

    def _show_step_oauth_credentials(self, errors):
        webhook_url = get_webhook_url(self.hass)
        return self.async_show_form(
            step_id="oauth_credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APP_ID): str,
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "developer_url": "https://smartthings.developer.samsung.com/",
                "webhook_url": webhook_url,
            },
        )

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Wait for the user to authorize the app installation."""
        user_input = {} if user_input is None else user_input
        self.installed_app_id = user_input.get(CONF_INSTALLED_APP_ID)
        self.refresh_token = user_input.get(CONF_REFRESH_TOKEN)

        # The OAuth callback includes the location chosen by the user in SmartThings.
        if CONF_LOCATION_ID in user_input:
            self.location_id = user_input[CONF_LOCATION_ID]

        if self.installed_app_id is None:
            # Launch the external setup URL.
            # location_id may not be known yet for OAuth flows; SmartThings will
            # let the user pick a location on its own authorization page.
            location_id = getattr(self, "location_id", "") or ""
            url = format_install_url(self.app_id, location_id)
            return self.async_external_step(step_id="authorize", url=url)

        # Set the unique_id now that we have both app_id and location_id.
        if not self.context.get("unique_id"):
            await self.async_set_unique_id(
                format_unique_id(self.app_id, self.location_id)
            )
            self._abort_if_unique_id_configured()

        next_step_id = "install"
        if self.source == SOURCE_REAUTH:
            next_step_id = "update"
        return self.async_external_step_done(next_step_id=next_step_id)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication of an existing config entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication of an existing config entry."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        entry = self._get_reauth_entry()
        self.app_id = entry.data[CONF_APP_ID]
        self.location_id = entry.data[CONF_LOCATION_ID]
        self.oauth_client_id = entry.data[CONF_CLIENT_ID]
        self.oauth_client_secret = entry.data[CONF_CLIENT_SECRET]
        self._set_confirm_only()
        return await self.async_step_authorize()

    async def async_step_update(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication of an existing config entry."""
        return await self.async_step_update_confirm()

    async def async_step_update_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication of an existing config entry."""
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(step_id="update_confirm")
        entry = self._get_reauth_entry()
        return self.async_update_reload_and_abort(
            entry, data_updates={CONF_REFRESH_TOKEN: self.refresh_token}
        )

    async def async_step_install(self, data=None):
        """Create a config entry at completion of a flow and authorization of the app."""
        session = async_get_clientsession(self.hass)

        # Exchange the refresh token for a fresh access token.
        api = SmartThings(session, "")
        token = await api.generate_tokens(
            self.oauth_client_id,
            self.oauth_client_secret,
            self.refresh_token,
        )

        config_data = {
            CONF_ACCESS_TOKEN: token.access_token,
            CONF_REFRESH_TOKEN: token.refresh_token,
            CONF_CLIENT_ID: self.oauth_client_id,
            CONF_CLIENT_SECRET: self.oauth_client_secret,
            CONF_LOCATION_ID: self.location_id,
            CONF_APP_ID: self.app_id,
            CONF_INSTALLED_APP_ID: self.installed_app_id,
        }

        # Fetch the location name to use as the config entry title.
        api = SmartThings(session, token.access_token)
        location = await api.location(config_data[CONF_LOCATION_ID])

        return self.async_create_entry(title=location.name, data=config_data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        #self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] = None) -> dict[str, Any]:
        errors: dict[str, str] = {}
        """Handle options flow."""
        options = self.config_entry.options

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                    {
                        #vol.Optional(CONF_ENABLE_DEFAULT_ENTITIES, default=options.get(CONF_ENABLE_DEFAULT_ENTITIES, False)): cv.boolean,
                        vol.Optional(CONF_ENABLE_SYNTAX_PROPERTY, default=options.get(CONF_ENABLE_SYNTAX_PROPERTY, False)): cv.boolean,
                        vol.Optional(CONF_RESETTING_ENTITIES, default=options.get(CONF_RESETTING_ENTITIES, False)): cv.boolean,
                    }
            ), errors=errors
        )
        
