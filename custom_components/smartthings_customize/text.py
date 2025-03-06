"""Support for texts through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .pysmartthings import Capability
from .pysmartthings.device import Status

from homeassistant.components.text import TextEntity, TextMode, MAX_LENGTH_STATE_STATE, ATTR_MAX, ATTR_MIN, ATTR_MODE, ATTR_PATTERN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    settings = SettingManager.get_capa_settings(broker, Platform.TEXT)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsText_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsText_custom(SmartThingsEntity_custom, TextEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.TEXT, setting=setting)

    @property
    def mode(self) -> TextMode:
        return self.get_attr_value(Platform.TEXT, ATTR_MODE, TextMode.TEXT)

    @property
    def native_max(self) -> int:
        return self.get_attr_value(Platform.TEXT, ATTR_MAX, MAX_LENGTH_STATE_STATE)

    @property
    def native_min(self) -> int:
        return self.get_attr_value(Platform.TEXT, ATTR_MIN, 0)

    @property
    def pattern(self) -> str | None:
        return self.get_attr_value(Platform.TEXT, ATTR_PATTERN, "")

    @property
    def native_value(self) -> str | None:
        return self.get_attr_value(Platform.TEXT, CONF_STATE, "")

    async def async_set_value(self, value: str) -> None:
        arg = []
        if self.get_command(Platform.TEXT) == "bixbyCommand":
            arg.append("search_all")
        arg.append(value)
        await self.send_command(Platform.TEXT, self.get_command(Platform.TEXT), arg)
