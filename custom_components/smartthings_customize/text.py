"""Support for texts through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.text import TextEntity
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
    settings = SettingManager.get_capa_settings(broker, "texts")
    for s in settings:
        entities.append(SmartThingsText_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("attribute"),
                                                    s[2].get("command"),
                                                    s[2].get("argument"),
                                                    s[2].get("parent_entity_id"),
                                                    s[1].get("min"),
                                                    s[1].get("max"),
                                                    s[1].get("pattern"),
                                                    s[1].get("mode"),
        ))

    async_add_entities(entities)

class SmartThingsText_custom(SmartThingsEntity_custom, TextEntity):
    def __init__(self, hass, device, name:str, component:str, capability: str, attribute: str, command:str, argument:str, parent_entity_id:str, min:float, max:float, pattern:str, mode: str) -> None:
        super().__init__(hass, "number", device, name, component, capability, attribute, command, argument, parent_entity_id)
        self._min = min
        self._max = max
        self._pattern = pattern
        self._mode = mode
        
        self._extra_state_attributes["min"] = self._min if self._min != None else 0
        self._extra_state_attributes["max"] = self._max if self._max != None else 255
        self._extra_state_attributes["pattern"] = self._pattern if self._pattern != None else ""
        self._extra_state_attributes["mode"] = self._mode if self._mode != None else "text"

    @property
    def mode(self) -> TextMode:
        return self._mode if self._mode != None else "text"

    @property
    def native_max(self) -> int:
        return self._max if self._max != None else 255

    @property
    def native_min(self) -> int:
        return self._min if self._min != None else 0

    @property
    def pattern(self) -> str | None:
        return self._pattern if self._pattern != None else ""

    @property
    def native_value(self) -> str | None:
        if self._attribute == "text":
            return ""
        return get_attribute(self._device, self._component, self._attribute).value

    @property
    def set_value(self) -> str | None:
        return get_attribute(self._device, self._component, self._attribute).value

    async def async_set_value(self, value: str) -> None:
        arg = []
        if self._command == "bixbyCommand":
            arg.append("search_all")
        arg.append(value)
        await self._device.command(
            self._component, self._capability, self._command, arg)
