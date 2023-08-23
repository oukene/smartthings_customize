"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.number import NumberEntity, NumberMode
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

    if broker._settings != None:
        for cap in broker._settings.get("numbers"):
            for device in broker.devices.values():
                if broker.is_allow_device(device.device_id) == False:
                    continue
                if cap.get("capability") in device.capabilities:
                    for command in cap.get("commands"):
                        _LOGGER.debug("add numbers : " + str(command))
                        entities.append(
                            SmartThingsNumber_custom(device,
                                                cap.get("component"),
                                                cap.get("capability"),
                                                command.get("name"),
                                                command.get("command"),
                                                command.get("attribute"),
                                                cap.get("min"),
                                                cap.get("max"),
                                                cap.get("step"),
                                                cap.get("mode"),
                                                )
                            )

    async_add_entities(entities)

class SmartThingsNumber_custom(SmartThingsEntity, NumberEntity):
    def __init__(self, device, component, capability: str, name:str, command:str, attribute: str, min, max, step, mode: str) -> None:
        super().__init__(device)
        self._component = component
        self._capability = capability
        self._name = name
        self._command = command
        self._attribute = attribute
        self._min = min
        self._max = max
        self._step = step
        self._mode = mode

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._command}"

    @property
    def mode(self) -> NumberMode:
        return self._mode

    @property
    def native_min_value(self) -> float:
        if str(type(self._min)) == "<class 'dict'>":
            if self._component == "main":
                min = self._device.status.attributes[self._min["attribute"]].value
            else:
                min = self._device.status._components[self._component].attributes.get(self._min["attribute"]).value
        else:
            min = self._min
        return min

    @property
    def native_max_value(self) -> float:
        if str(type(self._max)) == "<class 'dict'>":
            if self._component == "main":
                max = self._device.status.attributes[self._max["attribute"]].value
            else:
                max = self._device.status._components[self._component].attributes.get(self._max["attribute"]).value
        else:
            max = self._max
        return max

    @property
    def native_step(self) -> float | None:
        return self._step

    async def async_set_native_value(self, value: float) -> None:
        arg = []
        arg.append(value)
        if await self._device.command(
            self._component, self._capability, self._command, arg
        ):
            self.async_write_ha_state()


    @property
    def native_value(self) -> float | None:
        if self._component == "main":
            return self._device.status.attributes[self._attribute].value
        else:
            return self._device.status._components[self._component].attributes.get(self._attribute).value

