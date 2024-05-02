"""Support for texts through the SmartThings cloud API."""
from __future__ import annotations

from homeassistant.components.update import (
    UpdateEntity, TYPE_CHECKING, UpdateEntityFeature, ATTR_INSTALLED_VERSION, ATTR_LATEST_VERSION,
    ATTR_RELEASE_SUMMARY, ATTR_RELEASE_URL, ATTR_TITLE, ATTR_AUTO_UPDATE, UpdateDeviceClass, ATTR_IN_PROGRESS
)
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.const import ATTR_DEVICE_CLASS
from .common import *

from functools import cached_property


import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add update for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]

    entities = []
    settings = SettingManager.get_capa_settings(broker, Platform.UPDATE)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsUpdate_custom(hass=hass, setting=s))

    async_add_entities(entities)

class SmartThingsUpdate_custom(SmartThingsEntity_custom, UpdateEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.UPDATE, setting=setting)
        self._attr_device_class = self.get_attr_value(Platform.UPDATE, ATTR_DEVICE_CLASS, UpdateDeviceClass.FIRMWARE)
        self._attr_auto_update = self.get_attr_value(Platform.UPDATE, ATTR_AUTO_UPDATE, False)
        self._new_version_available = self.get_attr_value(Platform.UPDATE, "update_available")

        self._attr_supported_features = UpdateEntityFeature(0)
        if self.get_command(Platform.UPDATE):
            self._attr_supported_features |= UpdateEntityFeature.INSTALL

        if self.get_attr_value(Platform.UPDATE, ATTR_IN_PROGRESS):
            self._attr_supported_features |= UpdateEntityFeature.PROGRESS
        
        if self.get_attr_value(Platform.UPDATE, ATTR_RELEASE_SUMMARY) or self.get_attr_value(Platform.UPDATE, ATTR_RELEASE_URL) != None:
            self._attr_supported_features |= UpdateEntityFeature.RELEASE_NOTES

    @cached_property
    def installed_version(self) -> str | None:
        if self._new_version_available != None:
            return False
        else:
            return self.get_attr_value(Platform.UPDATE, ATTR_INSTALLED_VERSION)

    @cached_property
    def latest_version(self) -> str | None:
        if self._new_version_available != None:
            return self._new_version_available
        else:
            return self.get_attr_value(Platform.UPDATE, ATTR_LATEST_VERSION)

    @cached_property
    def in_progress(self) -> bool | int | None:
        return self.get_attr_value(Platform.UPDATE, ATTR_IN_PROGRESS)

    @cached_property
    def release_summary(self) -> str | None:
        return self.get_attr_value(Platform.UPDATE, ATTR_RELEASE_SUMMARY)

    @cached_property
    def release_url(self) -> str | None:
        return self.get_attr_value(Platform.UPDATE, ATTR_RELEASE_URL)

    @cached_property
    def title(self) -> str | None:
        return self.get_attr_value(Platform.UPDATE, ATTR_TITLE)

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        return self.send_command(Platform.UPDATE, self.get_command(Platform.UPDATE), [])

    async def async_release_notes(self) -> str | None:
        return self.get_attr_value(Platform.UPDATE, ATTR_RELEASE_URL)
