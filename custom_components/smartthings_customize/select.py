"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.select import SelectEntity
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
        _LOGGER.debug("start customize select entity start size : %d", len(broker._settings.get("selects")))
        for cap in broker._settings.get("selects"):
            for device in broker.devices.values():
                if broker.is_allow_device(device.device_id) == False:
                    continue
                if cap.get("capability") in device.capabilities:
                    for command in cap.get("commands"):
                        _LOGGER.debug("add select : " + str(command))
                        entities.append(
                            SmartThingsSelect_custom(device,
                                                cap.get("component"),
                                                cap.get("capability"),
                                                command.get("name"),
                                                command.get("command"),
                                                command.get("attribute"),
                                                cap.get("options")
                                                )
                            )
    except:
        _LOGGER.debug("check setting file")
    async_add_entities(entities)

class SmartThingsSelect_custom(SmartThingsEntity, SelectEntity):
    def __init__(self, device, component, capability: str, name:str, command:str, attribute: str, options) -> None:
        super().__init__(device)
        self._component = component
        self._capability = capability
        self._name = name
        self._command = command
        self._attribute = attribute
        self._options = options

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._command}"

    @property
    def options(self) -> list[str]:
        if str(type(self._options)) == "<class 'dict'>":
            if self._component == "main":
                opt = self._device.status.attributes[self._options["attribute"]].value
            else:
                opt = self._device.status._components[self._component].attributes.get(self.options["attribute"]).value if self._device.status._components.get(self._component) else []
        else:
            opt = self._options
        return opt

    @property
    def current_option(self) -> str | None:
        if self._component == "main":
            return self._device.status.attributes[self._attribute].value
        else:
            return self._device.status._components[self._component].attributes.get(self._attribute).value if self._device.status._components.get(self._component) else ""

    async def async_select_option(self, option: str) -> None:
        arg = []
        arg.append(option)
        if await self._device.command(
            self._component, self._capability, self._command, arg
        ):
            self.async_write_ha_state()

