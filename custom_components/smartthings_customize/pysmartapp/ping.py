"""Define the ping module."""

from .request import Request, Response


class PingRequest(Request):
    """Defines a ping request."""

    def __init__(self, data: dict):
        """Create a new instance of the PingRequest class."""
        super().__init__(data)
        self._supports_validation = False
        self._ping_data_raw = data['pingData']

    async def _process(self, app):
        response = PingResponse()
        response.ping_challenge = self.ping_challenge
        return response

    @property
    def ping_data_raw(self) -> dict:
        """Get the raw data structure of the ping request."""
        return self._ping_data_raw

    @property
    def ping_challenge(self):
        """Get the challenge code as part of the request."""
        return self._ping_data_raw['challenge']


class PingResponse(Response):
    """Defines a ping response."""

    def __init__(self):
        """Create a new instance of the PingResponse."""
        self._ping_challenge = None

    def to_data(self) -> dict:
        """Create a data structure for the response."""
        return {'pingData': {'challenge': self.ping_challenge}}

    @property
    def ping_challenge(self):
        """Get the ping challenge in the response."""
        return self._ping_challenge

    @ping_challenge.setter
    def ping_challenge(self, value: str):
        """Set the ping challenge response."""
        self._ping_challenge = value
