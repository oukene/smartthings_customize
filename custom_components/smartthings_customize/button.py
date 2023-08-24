"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity
from .const import DATA_BROKERS, DOMAIN

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

    try:
        _LOGGER.debug("start customize button entity start size : %d", len(broker._settings.get("buttons")))
        for cap in broker._settings.get("buttons"):
            for device in broker.devices.values():
                if broker.is_allow_device(device.device_id) == False:
                    continue
                capabilities = broker.build_capability(device)
                for key, value in capabilities.items():
                    if cap.get("component") == key and cap.get("capability") in value:
                        for command in cap.get("commands"):
                            _LOGGER.debug("add button : " + str(command))
                            entities.append(
                                SmartThingsButton_custom(device,
                                                    cap.get("component"),
                                                    cap.get("capability"),
                                                    command.get("name"),
                                                    command.get("command"),
                                                    command.get("argument"),
                                                    )
                                )
    except:
        pass
    async_add_entities(entities)

class SmartThingsButton_custom(SmartThingsEntity, ButtonEntity):
    def __init__(self, device, component, capability: str, name:str, command:str, argument:str) -> None:
        super().__init__(device)
        self._component = component
        self._capability = capability
        self._name = name
        self._command = command
        self._argument = argument
    #     self._extra_state_attributes["component"] = component
    #     self._extra_state_attributes["capability"] = capability
    #     self._extra_state_attributes["command"] = command
    #     self._extra_state_attributes["argument"] = argument

    # @property
    # def extra_state_attributes(self):
    #     return self._extra_state_attributes

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._capability}.{self._command}"

    async def async_press(self) -> None:
        await self._device.command(
            self._component, self._capability, self._command, self._argument)

    