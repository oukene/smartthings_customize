"""Define a SmartApp."""

import logging
from typing import Any, Callable, Dict, List

from .const import (
    LIFECYCLE_CONFIG, LIFECYCLE_EVENT, LIFECYCLE_INSTALL,
    LIFECYCLE_OAUTH_CALLBACK, LIFECYCLE_PING, LIFECYCLE_UNINSTALL,
    LIFECYCLE_UPDATE, SETTINGS_APP_ID)
from .dispatch import Dispatcher
from .errors import SmartAppNotRegisteredError
from .utilities import create_request

_LOGGER = logging.getLogger(__name__)


class SmartAppBase:
    """Define common functionality for the SmartApp and SmartAppManager."""

    def __init__(self, *, path: str = '/', dispatcher: Dispatcher = None):
        """Initialize a new instance of the smartapp."""
        self._dispatcher = dispatcher or Dispatcher()
        self._path = path

    def connect_ping(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the ping signal."""
        return self._dispatcher.connect(LIFECYCLE_PING, target)

    def connect_config(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the config signal."""
        return self._dispatcher.connect(LIFECYCLE_CONFIG, target)

    def connect_install(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the install signal."""
        return self._dispatcher.connect(LIFECYCLE_INSTALL, target)

    def connect_update(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the update signal."""
        return self._dispatcher.connect(LIFECYCLE_UPDATE, target)

    def connect_event(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the event signal."""
        return self._dispatcher.connect(LIFECYCLE_EVENT, target)

    def connect_oauth_callback(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the oauth callback signal."""
        return self._dispatcher.connect(LIFECYCLE_OAUTH_CALLBACK, target)

    def connect_uninstall(self, target: Callable[..., Any]) \
            -> Callable[[], None]:
        """Connect a target to the oauth callback signal."""
        return self._dispatcher.connect(LIFECYCLE_UNINSTALL, target)

    @property
    def path(self) -> str:
        """Get the path the SmartApp is installed at."""
        return self._path

    @property
    def dispatcher(self):
        """Get the dispatcher used to connect and send notifications."""
        return self._dispatcher


class SmartApp(SmartAppBase):
    """Define the SmartApp class."""

    def __init__(self, *, path: str = '/', public_key=None,
                 dispatcher: Dispatcher = None):
        """Initialize the SmartApp class."""
        super().__init__(path=path, dispatcher=dispatcher)
        self._app_id = None
        self._config_app_id = 'app'
        self._description = None
        self._name = None
        self._permissions = []
        self._public_key = public_key

    async def handle_request(self, data: dict, headers: dict = None,
                             validate_signature: bool = True) -> dict:
        """Process a lifecycle event."""
        req = create_request(data)
        resp = await req.process(self, headers, validate_signature)

        if req.installed_app_id:
            _LOGGER.debug("%s: %s received for installed app %s.",
                          req.execution_id, req.lifecycle,
                          req.installed_app_id)
        else:
            _LOGGER.debug("%s: %s received.",
                          req.execution_id, req.lifecycle)

        return resp.to_data()

    @property
    def app_id(self):
        """Get the unique id of the SmartApp."""
        return self._app_id

    @app_id.setter
    def app_id(self, value: str):
        """Set the app id of the SmartApp."""
        self._app_id = value

    @property
    def name(self) -> str:
        """Get the name of the SmartApp using during config."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the SmartApp used during config."""
        self._name = value

    @property
    def description(self) -> str:
        """Get the description of the SmartApp used during config."""
        return self._description

    @description.setter
    def description(self, value: str):
        """Set the description of the SmartApp used during config."""
        self._description = value

    @property
    def config_app_id(self):
        """Get the id for the SmartApp used during config."""
        return self._config_app_id

    @config_app_id.setter
    def config_app_id(self, value: str):
        """Set the id of the SmartApp used during config."""
        self._config_app_id = value

    @property
    def permissions(self) -> List[str]:
        """Get the permissions of the SmartApp used during config."""
        return self._permissions

    @property
    def public_key(self):
        """Get the public key of the SmartApp used to verify events."""
        return self._public_key


class SmartAppManager(SmartAppBase):
    """Service to support multiple SmartApps at the same end-point."""

    def __init__(self, path: str, *, dispatcher: Dispatcher = None):
        """Create a new instance of the manager."""
        super().__init__(path=path, dispatcher=dispatcher)
        self._smartapps = {}

    async def handle_request(self, data: dict, headers: dict = None,
                             validate_signature: bool = True) -> dict:
        """Process a lifecycle event."""
        req = create_request(data)
        # Always process ping lifecycle events.
        if req.lifecycle == LIFECYCLE_PING:
            resp = await req.process(self, headers, validate_signature)
        else:
            app_id = req.settings.get(SETTINGS_APP_ID)
            if not app_id:
                raise SmartAppNotRegisteredError(req.installed_app_id)
            smartapp = self._smartapps.get(app_id)
            if not smartapp:
                raise SmartAppNotRegisteredError(req.installed_app_id)
            resp = await req.process(smartapp, headers, validate_signature)

        if req.installed_app_id:
            _LOGGER.debug("%s: %s received for installed app %s.",
                          req.execution_id, req.lifecycle,
                          req.installed_app_id)
        else:
            _LOGGER.debug("%s: %s received.",
                          req.execution_id, req.lifecycle)
        return resp.to_data()

    def register(self, app_id: str, public_key: str) -> SmartApp:
        """Create a new SmartApp for the end-point."""
        if app_id is None:
            raise ValueError('smartapp must have an app_id.')
        if app_id in self._smartapps:
            raise ValueError('smartapp already registered.')
        smartapp = SmartApp(
            path=self._path,
            public_key=public_key,
            dispatcher=self._dispatcher
        )
        smartapp.app_id = app_id
        self._smartapps[smartapp.app_id] = smartapp
        return smartapp

    def unregister(self, app_id: str):
        """Unregister the specified installed app id."""
        if app_id is None:
            raise ValueError('smartapp must have an app_id.')
        if app_id not in self._smartapps:
            raise ValueError('smartapp was not previously registered.')
        self._smartapps.pop(app_id, None)

    @property
    def smartapps(self) -> Dict[str, SmartApp]:
        """Get registered SmartApps."""
        return self._smartapps
