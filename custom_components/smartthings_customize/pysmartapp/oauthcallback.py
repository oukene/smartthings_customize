"""Define the oauthcallback module."""

from .request import EmptyDataResponse, Request, Response


class OAuthCallbackRequest(Request):
    """Define the OAuthCallbackRequest class."""

    def __init__(self, data: dict):
        """Create a new instance of the OAuthCallbackRequest."""
        super().__init__(data)
        callback_data = self._oauth_callback_data_raw = \
            data['oAuthCallbackData']
        self._installed_app_id = callback_data['installedAppId']
        self._url_path = callback_data['urlPath']

    async def _process(self, app) -> Response:
        resp = EmptyDataResponse('oAuthCallbackData')
        return resp

    @property
    def oauth_callback_data_raw(self) -> dict:
        """Get the raw OAuth Callback data."""
        return self._oauth_callback_data_raw

    @property
    def url_path(self) -> str:
        """Get the url path of the OAuth callback."""
        return self._url_path
