"""Define the update module."""

from .request import EmptyDataResponse, Request, Response


class UpdateRequest(Request):
    """Define the UpdateRequest class."""

    def __init__(self, data: dict):
        """Create a new instance of the UpdateRequest."""
        super().__init__(data)
        update_data = self._update_data_raw = data['updateData']
        self._init_installed_app(update_data['installedApp'])
        self._auth_token = update_data['authToken']
        self._refresh_token = update_data['refreshToken']

    async def _process(self, app) -> Response:
        resp = EmptyDataResponse('updateData')
        return resp

    @property
    def update_data_raw(self) -> dict:
        """Get the raw update data."""
        return self._update_data_raw

    @property
    def auth_token(self):
        """Get the auth token."""
        return self._auth_token

    @property
    def refresh_token(self):
        """Get the refresh token."""
        return self._refresh_token
