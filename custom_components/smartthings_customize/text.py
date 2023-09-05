"""Support for texts through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.text import TextEntity, TextMode, MAX_LENGTH_STATE_STATE, ATTR_MAX, ATTR_MIN, ATTR_MODE, ATTR_PATTERN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity_custom
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
    settings = SettingManager.get_capa_settings(broker, CUSTOM_PLATFORMS[Platform.TEXT])
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsText_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsText_custom(SmartThingsEntity_custom, TextEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.TEXT, setting=setting)

        self._min = setting[1].get(ATTR_MIN) if setting[1].get(ATTR_MIN) != None else 0
        self._max = setting[1].get(ATTR_MAX) if setting[1].get(ATTR_MAX) != None else MAX_LENGTH_STATE_STATE
        self._pattern = setting[1].get(ATTR_PATTERN) if setting[1].get(ATTR_PATTERN) != None else ""
        self._mode = setting[1].get(ATTR_MODE) if setting[1].get(ATTR_MODE) != None else TextMode.TEXT

    @property
    def mode(self) -> TextMode:
        return self._mode

    @property
    def native_max(self) -> int:
        return self._max

    @property
    def native_min(self) -> int:
        return self._min

    @property
    def pattern(self) -> str | None:
        return self._pattern

    @property
    def native_value(self) -> str | None:
        value = get_attribute_value(self._device, self._component, self._capability, self._attribute)
        return value if value != None else ""

    async def async_set_value(self, value: str) -> None:
        arg = []
        if self._command == "bixbyCommand":
            arg.append("search_all")
        arg.append(value)
        await self._device.command(
            self._component, self._capability, self._command, arg)