"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

import yaml
import os
import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]

    entities = []

    for device in broker.devices.values():
        if broker.any_assigned(device.device_id, "switch"):
            entities.append(SmartThingsSwitch(device))

    with open(os.path.dirname(os.path.realpath(__file__)) + "/settings.yaml") as f:
        yaml_data = yaml.load(f, Loader=yaml.FullLoader)
        for cap in yaml_data["switches"]:
            for device in broker.devices.values():
                if cap["capability"] in device.capabilities:
                    for command in cap["commands"]:
                        _LOGGER.debug("add switch : " + str(command))
                        entities.append(
                            SmartThingsSwitch_ext(device,
                                                cap["component"],
                                                command["name"],
                                                cap["capability"],
                                                command["attribute"],
                                                command["command"],
                                                command["argument"],
                                                command["on_state"])
                            )

    async_add_entities(entities)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must be able to be turned on/off.
    if Capability.switch in capabilities:
        return [Capability.switch, Capability.energy_meter, Capability.power_meter]
    return None


class SmartThingsSwitch(SmartThingsEntity, SwitchEntity):

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.switch_off(set_status=True)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.switch_on(set_status=True)
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        return self._device.status.switch

class SmartThingsSwitch_ext(SmartThingsEntity, SwitchEntity):
    def __init__(self, device, component, name:str, capability: str, attribute: str, command:str, arguments:dict, on_state: str) -> None:
        super().__init__(device)
        self._component = component
        self._capability = capability
        self._name = name
        self._command = command
        self._attribute = attribute
        self._arguments = arguments
        self._on_state = on_state

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._command}"

    async def async_turn_off(self, **kwargs: Any) -> None:
        if await self._device.command(
            "main", self._capability, self._command, self._arguments["off"]
        ):
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if await self._device.command(
            "main", self._capability, self._command, self._arguments["on"]
        ):
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._device.status.attributes[self._attribute].value == self._on_state
