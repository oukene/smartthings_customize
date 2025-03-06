"""Define the install module."""

from .request import EmptyDataResponse, Request, Response


class InstallRequest(Request):
    """Define the InstallRequest class."""

    def __init__(self, data: dict):
        """Create a new instance of the InstallRequest."""
        super().__init__(data)
        install_data = self._install_data_raw = data['installData']
        self._init_installed_app(install_data['installedApp'])
        self._auth_token = install_data['authToken']
        self._refresh_token = install_data['refreshToken']

    async def _process(self, app) -> Response:
        resp = EmptyDataResponse('installData')
        return resp

    @property
    def install_data_raw(self) -> dict:
        """Get the raw installation data."""
        return self._install_data_raw

    @property
    def auth_token(self):
        """Get the auth token."""
        return self._auth_token

    @property
    def refresh_token(self):
        """Get the refresh token."""
        return self._refresh_token
