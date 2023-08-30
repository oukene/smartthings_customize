"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.number import NumberEntity, NumberMode, DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE, DEFAULT_STEP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity_custom
from .const import DATA_BROKERS, DOMAIN
from .common import SettingManager, get_attribute

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
    settings = SettingManager.get_capa_settings(broker, "numbers")
    for s in settings:
        entities.append(SmartThingsNumber_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("attribute"),
                                                    s[2].get("command"),
                                                    s[2].get("argument"),
                                                    s[2].get("parent_entity_id"),
                                                    s[2].get("min"),
                                                    s[2].get("max"),
                                                    s[2].get("step"),
                                                    s[2].get("mode"),
        ))

    async_add_entities(entities)

class SmartThingsNumber_custom(SmartThingsEntity_custom, NumberEntity):
    def __init__(self, hass, device, name:str, component:str, capability: str, attribute: str, command:str, argument:str, parent_entity_id:str, min:float, max:float, step:float, mode: str) -> None:
        super().__init__(hass, "number", device, name, component, capability, attribute, command, argument, parent_entity_id)
        self._min = min
        self._max = max
        self._step = step
        self._mode = mode
        
        self._extra_state_attributes["min"] = min
        self._extra_state_attributes["max"] = max
        self._extra_state_attributes["step"] = step
        self._extra_state_attributes["mode"] = mode

    @property
    def mode(self) -> NumberMode:
        return self._mode

    @property
    def native_min_value(self) -> float:
        if str(type(self._min)) == "<class 'dict'>":
            min = get_attribute(self._device, self._component, self._min["attribute"]).value
            min = min if min != None else DEFAULT_MIN_VALUE
        else:
            min = self._min
        return min

    @property
    def native_max_value(self) -> float:
        if str(type(self._max)) == "<class 'dict'>":
            max = get_attribute(self._device, self._component, self._max["attribute"]).value
            max = max if max != None else DEFAULT_MIN_VALUE
        else:
            max = self._max
        return max

    @property
    def native_step(self) -> float | None:
        return self._step

    @property
    def native_value(self) -> float | None:
        return get_attribute(self._device, self._component, self._attribute).value

    async def async_set_native_value(self, value: float) -> None:
        arg = []
        v = int(value) if value.is_integer() else value
        arg.append(v)
        await self._device.command(
            self._component, self._capability, self._command, arg)


