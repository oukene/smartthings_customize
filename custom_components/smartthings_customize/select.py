"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.select import SelectEntity
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
    settings = SettingManager.get_capa_settings(broker, "selects")
    for s in settings:
        entities.append(SmartThingsSelect_custom(hass,
                                                    s[0],
                                                    s[2].get("name"),
                                                    s[1].get("component"),
                                                    s[1].get("capability"),
                                                    s[2].get("attribute"),
                                                    s[2].get("command"),
                                                    s[2].get("argument"),
                                                    s[2].get("parent_entity_id"),
                                                    s[2].get("options"),
        ))

    async_add_entities(entities)

class SmartThingsSelect_custom(SmartThingsEntity_custom, SelectEntity):
    def __init__(self, hass, device, name:str, component:str, capability: str, attribute:str, command:str, argument:str, parent_entity_id:str, options) -> None:
        super().__init__(hass, "select", device, name, component, capability, attribute, command, argument, parent_entity_id)
        self._options = options

        self._extra_state_attributes["options"] = options

    @property
    def options(self) -> list[str]:
        if str(type(self._options)) == "<class 'dict'>":
            opt = get_attribute(self._device, self._component, self._options["attribute"]).value
            opt = opt if opt != None else []
        else:
            opt = self._options
        return opt

    @property
    def current_option(self) -> str | None:
        return get_attribute(self._device, self._component, self._attribute).value

    async def async_select_option(self, option: str) -> None:
        arg = []
        arg.append(option)
        await self._device.command(
            self._component, self._capability, self._command, arg)
        
