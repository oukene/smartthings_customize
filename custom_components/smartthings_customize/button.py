"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .common import *

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
    settings = SettingManager.get_capa_settings(broker, Platform.BUTTON)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsButton_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsButton_custom(SmartThingsEntity_custom, ButtonEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.BUTTON, setting=setting)
    
    async def async_press(self) -> None:
        await self.send_command(Platform.BUTTON, self.get_command(Platform.BUTTON), self.get_argument(Platform.BUTTON))

    
