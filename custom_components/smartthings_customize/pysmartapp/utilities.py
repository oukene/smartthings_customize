"""Define the utilities class."""

from .config import ConfigRequest
from .const import (
    LIFECYCLE_CONFIG, LIFECYCLE_EVENT, LIFECYCLE_INSTALL,
    LIFECYCLE_OAUTH_CALLBACK, LIFECYCLE_PING, LIFECYCLE_UNINSTALL,
    LIFECYCLE_UPDATE)
from .event import EventRequest
from .install import InstallRequest
from .oauthcallback import OAuthCallbackRequest
from .ping import PingRequest
from .uninstall import UninstallRequest
from .update import UpdateRequest


def create_request(data: dict):
    """Create a request from the given dictionary and headers."""
    lifecycle = data['lifecycle']
    if lifecycle == LIFECYCLE_PING:
        return PingRequest(data)
    if lifecycle == LIFECYCLE_CONFIG:
        return ConfigRequest(data)
    if lifecycle == LIFECYCLE_INSTALL:
        return InstallRequest(data)
    if lifecycle == LIFECYCLE_UPDATE:
        return UpdateRequest(data)
    if lifecycle == LIFECYCLE_EVENT:
        return EventRequest(data)
    if lifecycle == LIFECYCLE_OAUTH_CALLBACK:
        return OAuthCallbackRequest(data)
    if lifecycle == LIFECYCLE_UNINSTALL:
        return UninstallRequest(data)
    raise ValueError('The specified lifecycle event was not recognized.')
