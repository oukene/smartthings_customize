"""Support for binary sensors through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence

from pysmartthings import Attribute, Capability
from pysmartthings.device import DeviceEntity
from pysmartthings.capability import ATTRIBUTE_ON_VALUES

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN
import logging

CAPABILITY_TO_ATTRIB = {
    Capability.acceleration_sensor: Attribute.acceleration,
    Capability.contact_sensor: Attribute.contact,
    Capability.filter_status: Attribute.filter_status,
    Capability.motion_sensor: Attribute.motion,
    Capability.presence_sensor: Attribute.presence,
    Capability.sound_sensor: Attribute.sound,
    Capability.tamper_alert: Attribute.tamper,
    Capability.valve: Attribute.valve,
    Capability.water_sensor: Attribute.water,
}
ATTRIB_TO_CLASS = {
    Attribute.acceleration: BinarySensorDeviceClass.MOVING,
    Attribute.contact: BinarySensorDeviceClass.OPENING,
    Attribute.filter_status: BinarySensorDeviceClass.PROBLEM,
    Attribute.motion: BinarySensorDeviceClass.MOTION,
    Attribute.presence: BinarySensorDeviceClass.PRESENCE,
    Attribute.sound: BinarySensorDeviceClass.SOUND,
    Attribute.tamper: BinarySensorDeviceClass.PROBLEM,
    Attribute.valve: BinarySensorDeviceClass.OPENING,
    Attribute.water: BinarySensorDeviceClass.MOISTURE,
}
ATTRIB_TO_ENTTIY_CATEGORY = {
    Attribute.tamper: EntityCategory.DIAGNOSTIC,
}

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    sensors = []
    if broker.enable_official_component():
        for device in broker.devices.values():
            if broker.is_allow_device(device.device_id) == False:
                continue
            for capability in broker.get_assigned(device.device_id, "binary_sensor"):
                attrib = CAPABILITY_TO_ATTRIB[capability]
                sensors.append(SmartThingsBinarySensor(device, attrib))

    try:
        _LOGGER.debug("start customize binary sensor entity start size : %d", len(broker._settings.get("binary_sensors")))
        for cap in broker._settings.get("binary_sensors"):
            for device in broker.devices.values():
                if broker.is_allow_device(device.device_id) == False:
                    continue
                if cap.get("capability") in device.capabilities:
                    for attribute in cap["attributes"]:
                        sensors.append(
                            SmartThingsBinarySensor_custom(device,
                                                component=cap.get("component"),
                                                capability=cap.get("capability"),
                                                name=attribute.get("name"),
                                                attribute=attribute.get("attribute")
                                                )
                            )
    except:
        pass
    async_add_entities(sensors)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    return [
        capability for capability in CAPABILITY_TO_ATTRIB if capability in capabilities
    ]


class SmartThingsBinarySensor(SmartThingsEntity, BinarySensorEntity):
    """Define a SmartThings Binary Sensor."""

    def __init__(self, device, attribute):
        """Init the class."""
        super().__init__(device)
        self._attribute = attribute

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        return f"{self._device.label} {self._attribute}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.device_id}.{self._attribute}"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._device.status.is_on(self._attribute)

    @property
    def device_class(self):
        """Return the class of this device."""
        return ATTRIB_TO_CLASS[self._attribute]

    @property
    def entity_category(self):
        """Return the entity category of this device."""
        return ATTRIB_TO_ENTTIY_CATEGORY.get(self._attribute)


class SmartThingsBinarySensor_custom(SmartThingsBinarySensor):
    def __init__(
        self,
        device: DeviceEntity,
        component: str,
        capability: str,
        name: str,
        attribute: str
    ) -> None:
        """Init the class."""
        super().__init__(device, attribute)
        self._component = component
        self._name = name
        self._capability = capability

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._attribute}"

    @property
    def is_on(self):
        if self._component == "main":
            return self._device.status.is_on(self._attribute)
        else:
            value = self._device.status._components[self._component].attributes.get(self._attribute).value if self._device.status._components.get(self._component) else None
            if self._attribute not in ATTRIBUTE_ON_VALUES:
                return bool(value)
            return value == ATTRIBUTE_ON_VALUES[self._attribute]
