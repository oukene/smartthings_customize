"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity_custom
from .const import DATA_BROKERS, DOMAIN
from .common import SettingManager

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
    settings = SettingManager.get_capa_settings(broker, "buttons")
    for s in settings:
        entities.append(SmartThingsButton_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("command"),
                                                    s[2].get("argument"),
                                                    s[2].get("parent_entity_id"),
        ))

    async_add_entities(entities)

class SmartThingsButton_custom(SmartThingsEntity_custom, ButtonEntity):
    def __init__(self, hass, device, name:str, component, capability: str, command:str, argument:str, parent_entity_id) -> None:
        super().__init__(hass, "button", device, name, component, capability, None, command, argument, parent_entity_id )
    
    async def async_press(self) -> None:
        await self._device.command(
            self._component, self._capability, self._command, self._argument)

    