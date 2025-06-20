"""Config flow to configure SmartThings."""

from collections.abc import Mapping
from http import HTTPStatus
import logging
from typing import Any

from aiohttp import ClientResponseError
from .pysmartthings import APIResponseError, AppOAuth, SmartThings
from .pysmartthings.installedapp import format_install_url
import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import (
    APP_OAUTH_CLIENT_NAME,
    APP_OAUTH_SCOPES,
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
    create_app,
    find_app,
    format_unique_id,
    get_webhook_url,
    setup_smartapp,
    setup_smartapp_endpoint,
    update_app,
    validate_webhook_requirements,
)

_LOGGER = logging.getLogger(__name__)


class SmartThingsFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle configuration of SmartThings integrations."""

    VERSION = 2

    api: SmartThings
    app_id: str
    location_id: str

    def __init__(self) -> None:
        """Create a new instance of the flow handler."""
        self.access_token: str | None = None
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
        return await self.async_step_pat()

    async def async_step_pat(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Get the Personal Access Token and validate it."""
        errors: dict[str, str] = {}
        if user_input is None or CONF_ACCESS_TOKEN not in user_input:
            return self._show_step_pat(errors)

        self.access_token = user_input[CONF_ACCESS_TOKEN]

        # Ensure token is a UUID
        if not VAL_UID_MATCHER.match(self.access_token):
            errors[CONF_ACCESS_TOKEN] = "token_invalid_format"
            return self._show_step_pat(errors)

        # Setup end-point
        self.api = SmartThings(async_get_clientsession(self.hass), self.access_token)
        try:
            app = await find_app(self.hass, self.api)
            if app:
                await app.refresh()  # load all attributes
                await update_app(self.hass, app)
                # Find an existing entry to copy the oauth client
                existing = next(
                    (
                        entry
                        for entry in self._async_current_entries()
                        if entry.data[CONF_APP_ID] == app.app_id
                    ),
                    None,
                )
                if existing:
                    self.oauth_client_id = existing.data[CONF_CLIENT_ID]
                    self.oauth_client_secret = existing.data[CONF_CLIENT_SECRET]
                else:
                    # Get oauth client id/secret by regenerating it
                    app_oauth = AppOAuth(app.app_id)
                    app_oauth.client_name = APP_OAUTH_CLIENT_NAME
                    app_oauth.scope.extend(APP_OAUTH_SCOPES)
                    client = await self.api.generate_app_oauth(app_oauth)
                    self.oauth_client_secret = client.client_secret
                    self.oauth_client_id = client.client_id
            else:
                app, client = await create_app(self.hass, self.api)
                self.oauth_client_secret = client.client_secret
                self.oauth_client_id = client.client_id
            setup_smartapp(self.hass, app)
            self.app_id = app.app_id

        except APIResponseError as ex:
            if ex.is_target_error():
                errors["base"] = "webhook_error"
            else:
                errors["base"] = "app_setup_error"
            _LOGGER.exception(
                "API error setting up the SmartApp: %s", ex.raw_error_response
            )
            return self._show_step_pat(errors)
        except ClientResponseError as ex:
            if ex.status == HTTPStatus.UNAUTHORIZED:
                errors[CONF_ACCESS_TOKEN] = "token_unauthorized"
                _LOGGER.debug(
                    "Unauthorized error received setting up SmartApp", exc_info=True
                )
            elif ex.status == HTTPStatus.FORBIDDEN:
                errors[CONF_ACCESS_TOKEN] = "token_forbidden"
                _LOGGER.debug(
                    "Forbidden error received setting up SmartApp", exc_info=True
                )
            else:
                errors["base"] = "app_setup_error"
                _LOGGER.exception("Unexpected error setting up the SmartApp")
            return self._show_step_pat(errors)
        except Exception:
            errors["base"] = "app_setup_error"
            _LOGGER.exception("Unexpected error setting up the SmartApp")
            return self._show_step_pat(errors)

        return await self.async_step_select_location()

    async def async_step_select_location(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Ask user to select the location to setup."""
        if user_input is None or CONF_LOCATION_ID not in user_input:
            # Get available locations
            existing_locations = [
                entry.data[CONF_LOCATION_ID] for entry in self._async_current_entries()
            ]
            locations = await self.api.locations()
            locations_options = {
                location.location_id: location.name
                for location in locations
                if location.location_id not in existing_locations
            }
            if not locations_options:
                return self.async_abort(reason="no_available_locations")

            return self.async_show_form(
                step_id="select_location",
                data_schema=vol.Schema(
                    {vol.Required(CONF_LOCATION_ID): vol.In(locations_options)}
                ),
            )

        self.location_id = user_input[CONF_LOCATION_ID]
        await self.async_set_unique_id(format_unique_id(self.app_id, self.location_id))
        return await self.async_step_authorize()

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Wait for the user to authorize the app installation."""
        user_input = {} if user_input is None else user_input
        self.installed_app_id = user_input.get(CONF_INSTALLED_APP_ID)
        self.refresh_token = user_input.get(CONF_REFRESH_TOKEN)
        if self.installed_app_id is None:
            # Launch the external setup URL
            url = format_install_url(self.app_id, self.location_id)
            return self.async_external_step(step_id="authorize", url=url)

        next_step_id = "install"
        if self.source == SOURCE_REAUTH:
            next_step_id = "update"
        return self.async_external_step_done(next_step_id=next_step_id)

    def _show_step_pat(self, errors):
        if self.access_token is None:
            # Get the token from an existing entry to make it easier to setup multiple locations.
            self.access_token = next(
                (
                    entry.data.get(CONF_ACCESS_TOKEN)
                    for entry in self._async_current_entries()
                ),
                None,
            )

        return self.async_show_form(
            step_id="pat",
            data_schema=vol.Schema(
                {vol.Required(CONF_ACCESS_TOKEN, default=self.access_token): str}
            ),
            errors=errors,
            description_placeholders={
                "token_url": "https://account.smartthings.com/tokens",
                "component_url": (
                    "https://www.home-assistant.io/integrations/smartthings/"
                ),
            },
        )

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
        self.app_id = self._get_reauth_entry().data[CONF_APP_ID]
        self.location_id = self._get_reauth_entry().data[CONF_LOCATION_ID]
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
        data = {
            CONF_ACCESS_TOKEN: self.access_token,
            CONF_REFRESH_TOKEN: self.refresh_token,
            CONF_CLIENT_ID: self.oauth_client_id,
            CONF_CLIENT_SECRET: self.oauth_client_secret,
            CONF_LOCATION_ID: self.location_id,
            CONF_APP_ID: self.app_id,
            CONF_INSTALLED_APP_ID: self.installed_app_id,
        }

        location = await self.api.location(data[CONF_LOCATION_ID])
        self.location = location

        return self.async_create_entry(title=location.name, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

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
        
