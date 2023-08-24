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
    if broker.enable_official_component():
        for device in broker.devices.values():
            if broker.is_allow_device(device.device_id) == False:
                continue
            if broker.any_assigned(device.device_id, "switch"):
                entities.append(SmartThingsSwitch(device))

    try:
        _LOGGER.debug("start customize switch entity start size : %d", len(broker._settings.get("switches")))
        for cap in broker._settings.get("switches"):
            for device in broker.devices.values():
                if broker.is_allow_device(device.device_id) == False:
                    continue
                capabilities = broker.build_capability(device)
                for key, value in capabilities.items():
                    _LOGGER.debug("key : %s, value : %s, component : %s, cap : %s", key, value, cap.get("component"), cap.get("capability"))
                    if cap.get("component") == key and cap.get("capability") in value:
                        for command in cap.get("commands"):
                            _LOGGER.debug("add switch : " + str(command))
                            entities.append(
                                SmartThingsSwitch_custom(device,
                                                    cap.get("component"),
                                                    command.get("name"),
                                                    cap.get("capability"),
                                                    command.get("attribute"),
                                                    command.get("on_command"),
                                                    command.get("off_command"),
                                                    command.get("argument"),
                                                    command.get("on_state")
                                                    )
                                )
    except:
        pass
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

class SmartThingsSwitch_custom(SmartThingsSwitch):
    def __init__(self, device, component, name:str, capability: str, attribute: str, on_command:str, off_command:str, arguments:dict, on_state: str) -> None:
        super().__init__(device)
        self._component = component
        self._capability = capability
        self._name = name
        self._on_command = on_command
        self._off_command = off_command
        self._attribute = attribute
        self._arguments = arguments
        self._on_state = on_state

    @property
    def name(self) -> str:
        return f"{self._device.label} {self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._component}.{self._on_command}"

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._capability == "switch":
            await self._device.switch_off(set_status=True)
            self.async_write_ha_state()
        else:
            if await self._device.command(
                self._component, self._capability, self._off_command, self._arguments.get("off")
            ):
                self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self._capability == "switch":
            await self._device.switch_on(set_status=True)
            self.async_write_ha_state()
        else:
            if await self._device.command(
                self._component, self._capability, self._on_command, self._arguments.get("on")
            ):
                self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if self._component == "main":
            return self._device.status.attributes[self._attribute].value in self._on_state
        else:
            value = self._device.status._components[self._component].attributes.get(self._attribute).value if self._device.status._components.get(self._component) else None
            return value in self._on_state

                
