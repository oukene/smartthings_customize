"""Define the errors module."""


class SignatureVerificationError(Exception):
    """Defines an error for signature verification failures."""

    pass


class SmartAppNotRegisteredError(Exception):
    """Defines an error when a SmartApp isn't registered."""

    _message = "SmartApp handler for installed app '{}' was not found."

    def __init__(self, installed_app_id: str):
        """Create a new instance of the error."""
        Exception.__init__(self, self._message.format(installed_app_id))
        self._installed_app_id = installed_app_id

    @property
    def installed_app_id(self) -> str:
        """Get the installed app id not found."""
        return self._installed_app_id
