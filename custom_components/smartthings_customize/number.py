"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .pysmartthings import Capability

from homeassistant.components.number import NumberEntity, NumberMode, DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE, DEFAULT_STEP, ATTR_MIN, ATTR_MAX, ATTR_MODE, ATTR_STEP
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
    settings = SettingManager.get_capa_settings(broker, Platform.NUMBER)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsNumber_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsNumber_custom(SmartThingsEntity_custom, NumberEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.NUMBER, setting=setting)

    @property
    def mode(self) -> NumberMode:
        return self.get_attr_value(Platform.NUMBER, ATTR_MODE)

    @property
    def native_min_value(self) -> float:
        return self.get_attr_value(Platform.NUMBER, ATTR_MIN, DEFAULT_MIN_VALUE)

    @property
    def native_max_value(self) -> float:
        return self.get_attr_value(Platform.NUMBER, ATTR_MAX, DEFAULT_MAX_VALUE)

    @property
    def native_step(self) -> float | None:
        return self.get_attr_value(Platform.NUMBER, ATTR_STEP, DEFAULT_STEP)

    @property
    def native_value(self) -> float | None:
        return self.get_attr_value(Platform.NUMBER, CONF_STATE)

    async def async_set_native_value(self, value: float) -> None:
        arg = []
        v = int(value) if value.is_integer() else value
        arg.append(v)
        await self.send_command(Platform.NUMBER, self.get_command(Platform.NUMBER), arg)


