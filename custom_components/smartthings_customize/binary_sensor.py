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

from . import SmartThingsEntity, SmartThingsEntity_custom
from .const import DATA_BROKERS, DOMAIN
import logging
from .common import SettingManager, get_attribute

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
    if SettingManager.enable_default_entities():
        for device in broker.devices.values():
            if SettingManager.is_allow_device(device.device_id) == False:
                continue
            for capability in broker.get_assigned(device.device_id, "binary_sensor"):
                attrib = CAPABILITY_TO_ATTRIB[capability]
                sensors.append(SmartThingsBinarySensor(device, attrib))

    settings = SettingManager.get_capa_settings(broker, "binary_sensors")
    for s in settings:
        sensors.append(SmartThingsBinarySensor_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("attribute"),
                                                    s[2].get("parent_entity_id"),
        ))

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


class SmartThingsBinarySensor_custom(SmartThingsEntity_custom, BinarySensorEntity):
    def __init__(
        self,
        hass,
        device: DeviceEntity,
        name: str,
        component: str,
        capability: str,
        attribute: str,
        parent_entity_id: str
    ) -> None:
        """Init the class."""
        super().__init__(hass, "binary_sensor", device, name, component, capability, attribute, None, None, parent_entity_id)

    @property
    def device_class(self):
        """Return the class of this device."""
        return ATTRIB_TO_CLASS[self._attribute]

    @property
    def entity_category(self):
        """Return the entity category of this device."""
        return ATTRIB_TO_ENTTIY_CATEGORY.get(self._attribute)

    @property
    def is_on(self):
        value = get_attribute(self._device, self._component, self._attribute).value

        if self._attribute not in ATTRIBUTE_ON_VALUES:
            return bool(value)
        return value == ATTRIBUTE_ON_VALUES[self._attribute]
