"""Define the uninstall module."""

from .request import EmptyDataResponse, Request, Response


class UninstallRequest(Request):
    """Define the UninstallRequest class."""

    def __init__(self, data: dict):
        """Create a new instance of the UninstallRequest."""
        super().__init__(data)
        uninstall_data = self._uninstall_data_raw = data['uninstallData']
        self._init_installed_app(uninstall_data['installedApp'])

    async def _process(self, app) -> Response:
        resp = EmptyDataResponse('uninstallData')
        return resp

    @property
    def uninstall_data_raw(self) -> dict:
        """Get the raw update data."""
        return self._uninstall_data_raw
