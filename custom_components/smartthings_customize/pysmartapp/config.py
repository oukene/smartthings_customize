"""Define the configuration module."""

from typing import List

from .const import LIFECYCLE_CONFIG_INIT, LIFECYCLE_CONFIG_PAGE
from .request import Request, Response


class ConfigRequest(Request):
    """Defines a ConfigRequest."""

    def __init__(self, data: dict):
        """Create a new instance of the ConfigRequest."""
        super().__init__(data)
        config = self._config_data_raw = data['configurationData']
        self._installed_app_id = config['installedAppId']
        self._phase = config['phase']
        self._page_id = config['pageId']
        self._previous_page_id = config['previousPageId']

    async def _process(self, app) -> Response:
        if self._phase == LIFECYCLE_CONFIG_INIT:
            resp = self._process_init(app)
        elif self._phase == LIFECYCLE_CONFIG_PAGE:
            resp = self._process_page()
        else:
            raise ValueError("Invalid request configuration phase.")
        return resp

    @staticmethod
    def _process_init(app) -> Response:
        # This is a hard-coded primitive response.
        resp = ConfigInitResponse()
        resp.name = app.name
        resp.config_app_id = app.config_app_id
        resp.description = app.description
        resp.permissions.extend(app.permissions)
        resp.first_page_id = '1'
        return resp

    @staticmethod
    def _process_page() -> Response:
        # This is a hard-coded primitive response.
        resp = ConfigPageResponse()
        resp.page_id = '1'
        resp.name = 'Configuration'
        resp.complete = True
        resp.next_page_id = None
        resp.previous_page_id = None
        return resp

    @property
    def config_data_raw(self) -> dict:
        """Get the raw configuration data."""
        return self._config_data_raw

    @property
    def phase(self) -> str:
        """Get the current phase."""
        return self._phase

    @property
    def page_id(self) -> str:
        """Set the current page id."""
        return self._page_id

    @property
    def previous_page_id(self) -> str:
        """Get the previous page id."""
        return self._previous_page_id


class ConfigInitResponse(Response):
    """Define a configuration init response."""

    def __init__(self):
        """Create a new instance of the ConfigInitResponse."""
        self._name = None
        self._description = None
        self._config_app_id = None
        self._permissions = []
        self._first_page_id = "1"

    def to_data(self) -> dict:
        """Return a data structure representing the response."""
        return {
            "configurationData": {
                "initialize": {
                    "name": self.name,
                    "description": self.description,
                    "id": self.config_app_id,
                    "permissions": self.permissions,
                    "firstPageId": self.first_page_id
                }
            }
        }

    @property
    def name(self) -> str:
        """Get the name of the smartapp."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the smartapp."""
        self._name = value

    @property
    def description(self) -> str:
        """Get the description of the smartapp."""
        return self._description

    @description.setter
    def description(self, value: str):
        """Set the value of the smartapp."""
        self._description = value

    @property
    def config_app_id(self) -> str:
        """Get the id of the smartapp to use in config."""
        return self._config_app_id

    @config_app_id.setter
    def config_app_id(self, value: str):
        """Set the id of the smartapp to use in config."""
        self._config_app_id = value

    @property
    def permissions(self) -> List[str]:
        """Get the permissions the app requires."""
        return self._permissions

    @property
    def first_page_id(self) -> str:
        """Get the id of the first page."""
        return self._first_page_id

    @first_page_id.setter
    def first_page_id(self, value: str):
        """Set the id of the first page."""
        self._first_page_id = value


class ConfigPageResponse(Response):
    """Define a configuration page response."""

    def __init__(self):
        """Create a new instance of the ConfigPageResponse."""
        self._page_id = None
        self._name = None
        self._next_page_id = None
        self._previous_page_id = None
        self._complete = False

    def to_data(self) -> dict:
        """Return a data structure representing the response."""
        return {
            "configurationData": {
                "page": {
                    "pageId": self.page_id,
                    "name": self.name,
                    "nextPageId": self.next_page_id,
                    "previousPageId": self.previous_page_id,
                    "complete": self.complete,
                    "sections": []
                }
            }
        }

    @property
    def page_id(self) -> str:
        """Get the id of the page."""
        return self._page_id

    @page_id.setter
    def page_id(self, value: str):
        """Set the id of the page."""
        self._page_id = value

    @property
    def name(self) -> str:
        """Get the name of the configuration page."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of the configuration page."""
        self._name = value

    @property
    def next_page_id(self) -> str:
        """Get the id of the next page."""
        return self._next_page_id

    @next_page_id.setter
    def next_page_id(self, value: str):
        """Set the id of the next page."""
        self._next_page_id = value

    @property
    def previous_page_id(self) -> str:
        """Get the id of the previous page."""
        return self._previous_page_id

    @previous_page_id.setter
    def previous_page_id(self, value: str):
        """Set the id of the previous page."""
        self._previous_page_id = value

    @property
    def complete(self) -> bool:
        """Get whether this is the last config page."""
        return self._complete

    @complete.setter
    def complete(self, value: bool):
        """Set whether this is the last config page."""
        self._complete = value
