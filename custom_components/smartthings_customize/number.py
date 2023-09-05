"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.number import NumberEntity, NumberMode, DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE, DEFAULT_STEP, ATTR_MIN, ATTR_MAX, ATTR_MODE, ATTR_STEP
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
    settings = SettingManager.get_capa_settings(broker, CUSTOM_PLATFORMS[Platform.NUMBER])
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsNumber_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsNumber_custom(SmartThingsEntity_custom, NumberEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.NUMBER, setting=setting)

        self._min = setting[1].get(ATTR_MIN) if setting[1].get(ATTR_MIN) != None else DEFAULT_MIN_VALUE
        self._max = setting[1].get(ATTR_MAX) if setting[1].get(ATTR_MAX) != None else DEFAULT_MAX_VALUE
        self._step = setting[1].get(ATTR_STEP) if setting[1].get(ATTR_STEP) != None else DEFAULT_STEP
        self._mode = setting[1].get(ATTR_MODE) if setting[1].get(ATTR_MODE) != None else NumberMode.AUTO

    @property
    def mode(self) -> NumberMode:
        return self._mode

    @property
    def native_min_value(self) -> float:
        if str(type(self._min)) == "<class 'dict'>":
            capa = self._min.get(CONF_CAPABILITY) if self._min.get(CONF_CAPABILITY) != None else self._capability
            min = get_attribute_value(self._device, self._component, capa, self._min[CONF_ATTRIBUTE])
            min = min if min != None else DEFAULT_MIN_VALUE
        else:
            min = self._min
        return min

    @property
    def native_max_value(self) -> float:
        if str(type(self._max)) == "<class 'dict'>":
            capa = self._max.get(CONF_CAPABILITY) if self._max.get(CONF_CAPABILITY) != None else self._capability
            max = get_attribute_value(self._device, self._component, capa, self._max[CONF_ATTRIBUTE])
            max = max if max != None else DEFAULT_MAX_VALUE
        else:
            max = self._max
        return max

    @property
    def native_step(self) -> float | None:
        return self._step

    @property
    def native_value(self) -> float | None:
        return get_attribute_value(self._device, self._component, self._capability, self._attribute)

    async def async_set_native_value(self, value: float) -> None:
        arg = []
        v = int(value) if value.is_integer() else value
        arg.append(v)
        await self._device.command(
            self._component, self._capability, self._command, arg)


