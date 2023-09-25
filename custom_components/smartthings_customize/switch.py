"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.const import STATE_ON, STATE_OFF

from . import SmartThingsEntity
from .const import *

import logging
_LOGGER = logging.getLogger(__name__)

from .common import *


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
            if SettingManager.allow_device(device.device_id) == False:
                continue
            if broker.any_assigned(device.device_id, Platform.SWITCH):
                entities.append(SmartThingsSwitch(device))

    settings = SettingManager.get_capa_settings(broker, Platform.SWITCH)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsSwitch_custom(hass=hass, setting=s))

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
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.SWITCH,setting=setting)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.send_command(Platform.SWITCH, self.get_command(Platform.SWITCH, {STATE_OFF:STATE_OFF}).get(STATE_OFF), self.get_argument(Platform.SWITCH, {STATE_OFF:[STATE_OFF]}).get(STATE_OFF, []))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.send_command(Platform.SWITCH, self.get_command(Platform.SWITCH, {STATE_ON:STATE_ON}).get(STATE_ON), self.get_argument(Platform.SWITCH, {STATE_ON:[STATE_ON]}).get(STATE_ON, []))

    @property
    def is_on(self) -> bool:
        value = self.get_attr_value(Platform.SWITCH, CONF_STATE)
        on_state = self.get_attr_value(Platform.SWITCH, "on_state")
        return value in on_state

