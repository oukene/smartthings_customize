"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.select import SelectEntity
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
    settings = SettingManager.get_capa_settings(broker, Platform.SELECT)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsSelect_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsSelect_custom(SmartThingsEntity_custom, SelectEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.SELECT, setting=setting)

    @property
    def options(self) -> list[str]:
        return self.get_attr_value(Platform.SELECT, CONF_OPTIONS, [])

    @property
    def current_option(self) -> str | None:
        state = self.get_attr_value(Platform.SELECT, CONF_STATE)
        return self.get_mapping_value(Platform.SELECT, CONF_STATE_MAPPING, state)

    async def async_select_option(self, option: str) -> None:
        option = self.get_mapping_key(Platform.SELECT, CONF_STATE_MAPPING, option)
        arg = [option]
        await self.send_command(Platform.SELECT, self.get_command(Platform.SELECT), arg)
        
