"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity, SmartThingsEntity_custom
from .const import DATA_BROKERS, DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from .common import SettingManager, get_attribute

PLATFORM = "switch"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    entities = []

    if SettingManager.enable_default_entities():
        for device in broker.devices.values():
            if SettingManager.is_allow_device(device.device_id) == False:
                continue
            if broker.any_assigned(device.device_id, "switch"):
                entities.append(SmartThingsSwitch(device))

    settings = SettingManager.get_capa_settings(broker, "switches")
    for s in settings:
        entities.append(SmartThingsSwitch_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("attribute"),
                                                    s[2].get("on_command"),
                                                    s[2].get("off_command"),
                                                    s[2].get("argument"),
                                                    s[2].get("on_state"),
                                                    s[2].get("parent_entity_id"),
        ))


    async_add_entities(entities)

def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    # Must be able to be turned on/off.
    capa = []
    if Capability.switch in capabilities:
        capa.append(Capability.switch)
    if Capability.energy_meter in capabilities:
        capa.append(Capability.energy_meter)
    if Capability.power_meter in capabilities:
        capa.append(Capability.power_meter)
    
    return capa if len(capa) > 0 else None

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

class SmartThingsSwitch_custom(SmartThingsEntity_custom, SwitchEntity):
    def __init__(self, hass, device, name:str, component:str, capability: str, attribute: str, on_command:str, off_command:str, argument:dict, on_state: str, parent_entity_id:str) -> None:
        super().__init__(hass, "switch", device, name, component, capability, attribute, on_command, argument, parent_entity_id)
        self._off_command = off_command
        self._on_state = on_state
        self._extra_state_attributes["off command"] = off_command
        self._extra_state_attributes["on state"] = on_state


    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.command(
            self._component, self._capability, self._off_command, self._arguments.get("off") if self._capability != "switch" else [])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.command(
            self._component, self._capability, self._command, self._arguments.get("on") if self._capability != "switch" else [])

    @property
    def is_on(self) -> bool:
        value = get_attribute(self._device, self._component, self._attribute).value
        return value in self._on_state
