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
from .const import *
from .common import *

import logging
_LOGGER = logging.getLogger(__name__)

CONF_OPTIONS = "options"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]

    entities = []
    settings = SettingManager.get_capa_settings(broker, CUSTOM_PLATFORMS[Platform.SELECT])
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsSelect_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsSelect_custom(SmartThingsEntity_custom, SelectEntity):
    def __init__(self, hass, setting) -> None:

        super().__init__(hass, platform=Platform.SELECT, setting=setting)
        self._options = setting[1].get(CONF_OPTIONS)

    @property
    def options(self) -> list[str]:
        if str(type(self._options)) == "<class 'dict'>":
            capa = self._options.get(CONF_CAPABILITY) if self._options.get(CONF_CAPABILITY) != None else self._capability
            opt = get_attribute_value(self._device, self._component, capa, self._options[CONF_ATTRIBUTE])
            opt = opt if opt != None else []
        else:
            opt = self._options
        return opt

    @property
    def current_option(self) -> str | None:
        return get_attribute_value(self._device, self._component, self._capability, self._attribute)

    async def async_select_option(self, option: str) -> None:
        arg = []
        arg.append(option)
        await self._device.command(
            self._component, self._capability, self._command, arg)
        
