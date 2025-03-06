"""Define the event module."""

from typing import Any, Dict, Optional, Sequence

from .const import EVENT_TYPE_DEVICE, EVENT_TYPE_TIMER
from .request import EmptyDataResponse, Request, Response


class Event:
    """Define an event."""

    def __init__(self, data: dict):
        """Create a new instance of the event class."""
        self._event_type = data['eventType']
        self._subscription_name = None
        self._event_id = None
        self._location_id = None
        self._device_id = None
        self._component_id = None
        self._capability = None
        self._attribute = None
        self._value = None
        self._value_type = None
        self._data = None
        self._state_change = None
        if self._event_type == EVENT_TYPE_DEVICE:
            device_event = data['deviceEvent']
            self._subscription_name = device_event['subscriptionName']
            self._event_id = device_event['eventId']
            self._location_id = device_event['locationId']
            self._device_id = device_event['deviceId']
            self._component_id = device_event['componentId']
            self._capability = device_event['capability']
            self._attribute = device_event['attribute']
            self._value = device_event['value']
            self._value_type = device_event['valueType']
            self._data = device_event.get('data')
            self._state_change = device_event['stateChange']
        self._timer_name = None
        self._timer_type = None
        self._timer_time = None
        self._timer_expression = None
        if self._event_type == EVENT_TYPE_TIMER:
            timer_event = data['timerEvent']
            self._event_id = timer_event['eventId']
            self._timer_name = timer_event['name']
            self._timer_type = timer_event['type']
            self._timer_time = timer_event['time']
            self._timer_expression = timer_event['expression']

    @property
    def event_type(self) -> str:
        """Get the type of the event."""
        return self._event_type

    @property
    def subscription_name(self) -> str:
        """Get the subscription name."""
        return self._subscription_name

    @property
    def event_id(self) -> str:
        """Get the event id."""
        return self._event_id

    @property
    def location_id(self) -> str:
        """Get the location id."""
        return self._location_id

    @property
    def device_id(self) -> str:
        """Get the device id."""
        return self._device_id

    @property
    def component_id(self) -> str:
        """Get the component id."""
        return self._component_id

    @property
    def capability(self) -> str:
        """Get the capability."""
        return self._capability

    @property
    def attribute(self) -> str:
        """Get the attribute."""
        return self._attribute

    @property
    def value(self) -> Optional[Any]:
        """Get the value."""
        return self._value

    @property
    def value_type(self) -> str:
        """Get the type of the value."""
        return self._value_type

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """Get the data associated with the event."""
        return self._data

    @property
    def state_change(self) -> bool:
        """Get whether this is a new state change."""
        return self._state_change

    @property
    def timer_name(self) -> str:
        """Get the name of the timer schedule."""
        return self._timer_name

    @property
    def timer_type(self) -> str:
        """Get the type of time."""
        return self._timer_type

    @property
    def timer_time(self) -> str:
        """Get the time the timer fired."""
        return self._timer_time

    @property
    def timer_expression(self) -> str:
        """Get the timer firing expression."""
        return self._timer_expression


class EventRequest(Request):
    """Define the EventRequest class."""

    def __init__(self, data: dict):
        """Create a new instance of the EventRequest."""
        super().__init__(data)
        event_data = self._event_data_raw = data['eventData']
        self._auth_token = event_data['authToken']
        self._init_installed_app(event_data['installedApp'])
        self._events = [Event(item) for item in event_data['events']]

    async def _process(self, app) -> Response:
        resp = EmptyDataResponse('eventData')
        return resp

    @property
    def event_data_raw(self) -> dict:
        """Get the raw event data."""
        return self._event_data_raw

    @property
    def auth_token(self) -> str:
        """Get the auth token."""
        return self._auth_token

    @property
    def events(self) -> Sequence[Event]:
        """Get the events."""
        return self._events
