"""Define the request module."""
import os
import sys

from custom_components.smartthings_customize.httpsig.verify import HeaderVerifier
#from httpsig.verify import HeaderVerifier
from .errors import SignatureVerificationError


class Response:
    """Defines a response."""

    def to_data(self) -> dict:
        """Create a data structure for the response."""
        raise NotImplementedError


class EmptyDataResponse(Response):
    """Defines a response with an empty data structure."""

    def __init__(self, name: str):
        """Create a new instance of the EmptyDataResponse class."""
        self._name = name

    def to_data(self) -> dict:
        """Return a data structure representing this request."""
        return {self.name: {}}

    @property
    def name(self) -> str:
        """Get the name of the empty data tag."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the empty data tag."""
        self._name = value


class Request:
    """Defines a request to process."""

    def __init__(self, data: dict):
        """Create a new instance of the Request class."""
        self._lifecycle = data['lifecycle']
        self._execution_id = data['executionId']
        self._locale = data['locale']
        self._version = data['version']
        self._installed_app_id = None
        self._location_id = None
        self._installed_app_config = {}
        self._settings = data.get('settings', {})
        self._supports_validation = True

    def _init_installed_app(self, installed_app):
        self._installed_app_id = installed_app['installedAppId']
        self._location_id = installed_app['locationId']
        self._installed_app_config = installed_app['config']

    async def process(self, app, headers: list = None,
                      validate_signature: bool = True) -> Response:
        """Process the request with the SmartApp."""
        if validate_signature and self._supports_validation:
            try:
                verifier = HeaderVerifier(
                    headers=headers, secret=app.public_key, method='POST',
                    path=app.path)
                result = verifier.verify()
            except Exception as ex:
                raise SignatureVerificationError from ex
            if not result:
                raise SignatureVerificationError
        response = await self._process(app)
        app.dispatcher.send(self.lifecycle, self, response, app)
        return response

    async def _process(self, app) -> Response:
        raise NotImplementedError

    @property
    def lifecycle(self) -> str:
        """Get the lifecycle of the request."""
        return self._lifecycle

    @property
    def execution_id(self) -> str:
        """Get the execution id of the request."""
        return self._execution_id

    @property
    def locale(self) -> str:
        """Get the locale of the request."""
        return self._locale

    @property
    def version(self) -> str:
        """Get the version of the request."""
        return self._version

    @property
    def installed_app_id(self) -> str:
        """Get the installed app id the request is for."""
        return self._installed_app_id

    @property
    def location_id(self) -> str:
        """Get the installed app location id."""
        return self._location_id

    @property
    def installed_app_config(self) -> dict:
        """Get the installed app configuration."""
        return self._installed_app_config

    @property
    def settings(self):
        """Get the settings associated with the request."""
        return self._settings
