from .pysmartthings import SmartThings, DeviceEntity, Device, DeviceStatus, DeviceStatusBase
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from .pysmartthings.entity import Entity
from aiohttp import ClientSession
from typing import List, Optional, Sequence
from .pysmartthings.api import Api
from .pysmartthings.device import Status

import logging
_LOGGER = logging.getLogger(__name__)

class DeviceStatus_custom(DeviceStatus):
    def __init__(self, api: Api, device_id: str, data=None):
        """Create a new instance of the DeviceStatusEntity class."""
        super().__init__(api, device_id, data)
        self._api = api
        self._device_id = device_id
        self._components = {}
        self._status = {}
        if data:
            self.apply_data(data)

    def apply_attribute_update(
        self,
        component_id: str,
        capability: str,
        attribute: str,
        value: Any,
        unit: Optional[str] = None,
        data: Optional[Dict] = None,
    ):
        super().apply_attribute_update(component_id=component_id, capability=capability, attribute=attribute, value=value, unit=unit, data=data)
        old_status = self._status[component_id][capability][attribute]
        if component_id not in self._status:
            self._status[component_id] = {}
        if capability not in self._status[component_id]:
            self._status[component_id][capability] = {}
        self._status[component_id][capability][attribute] = Status(value, unit or old_status.unit, data)


    def apply_data(self, data: dict):
        super().apply_data(data=data)
        """Apply the values from the given data structure."""
        self._status.clear()
        for component_id, component in data["components"].items():
            #_LOGGER.error("component_id : " + str(component_id) + ", component : " + str(component))
            for capa, attributes in component.items():
                for attribute, value in attributes.items():
                    if component_id not in self._status:
                        self._status[component_id] = {}
                    if capa not in self._status[component_id]:
                        self._status[component_id][capa] = {}
                    self._status[component_id][capa][attribute] = Status(value.get("value"), value.get("unit"), value.get("data"))


class DeviceEntity_custom(DeviceEntity):
    def __init__(
        self, api: Api, data: Optional[dict] = None, device_id: Optional[str] = None
    ):
        """Create a new instance of the DeviceEntity class."""
        Entity.__init__(self, api)
        Device.__init__(self)
        if data:
            self.apply_data(data)
        if device_id:
            self._device_id = device_id
        self._status = DeviceStatus_custom(api, self._device_id)


class SmartThings_custom(SmartThings):

    async def devices(
        self,
        *,
        location_ids: Optional[Sequence[str]] = None,
        capabilities: Optional[Sequence[str]] = None,
        device_ids: Optional[Sequence[str]] = None
    ) -> List:
        """Retrieve SmartThings devices."""
        params = []
        if location_ids:
            params.extend([("locationId", lid) for lid in location_ids])
        if capabilities:
            params.extend([("capability", cap) for cap in capabilities])
        if device_ids:
            params.extend([("deviceId", did) for did in device_ids])
        resp = await self._service.get_devices(params)
        return [DeviceEntity_custom(self._service, entity) for entity in resp]

    async def device(self, device_id: str) -> DeviceEntity_custom:
        """Retrieve a device with the specified ID."""
        entity = await self._service.get_device(device_id)
        return DeviceEntity_custom(self._service, entity)
