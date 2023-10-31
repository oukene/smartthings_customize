"""Support for locks through the SmartThings cloud API."""
from __future__ import annotations


from collections.abc import Sequence
from typing import Any

from pysmartthings import Attribute, Capability

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


ST_CMD_LOCK = "lock"
ST_CMD_UNLOCK = "unlock"

from .const import *
from .common import *

from .lock import ST_LOCK_ATTR_MAP

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
    settings = SettingManager.get_capa_settings(broker, Platform.LOCK)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsLock_custom(hass=hass, setting=s))

    async_add_entities(entities)


class SmartThingsLock_custom(SmartThingsEntity_custom, LockEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.LOCK, setting=setting)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        await self.send_command(Platform.LOCK, self.get_command(Platform.LOCK, {ST_CMD_LOCK: ST_CMD_LOCK}).get(ST_CMD_LOCK), self.get_argument(Platform.LOCK, {ST_CMD_LOCK: []}).get(ST_CMD_LOCK, []))

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        await self.send_command(Platform.LOCK, self.get_command(Platform.LOCK, {ST_CMD_UNLOCK: ST_CMD_UNLOCK}).get(ST_CMD_UNLOCK), self.get_argument(Platform.LOCK, {ST_CMD_UNLOCK: []}).get(ST_CMD_UNLOCK, []))

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        value = self.get_attr_value(Platform.LOCK, CONF_STATE)
        lock_state = self.get_attr_value(Platform.LOCK, "lock_state")
        _LOGGER.error("is locked - value : " + str(value) + ", lock_state : " + str(lock_state))
        return value in lock_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        
        conf = self._capability[Platform.LOCK].get(CONF_STATE, [])
        status = self.get_attr_status(conf, Platform.LOCK)
        if status.value:
            self._extra_state_attributes["lock_state"] = status.value
        if isinstance(status.data, dict):
            for st_attr, ha_attr in ST_LOCK_ATTR_MAP.items():
                if (data_val := status.data.get(st_attr)) is not None:
                    self._extra_state_attributes[ha_attr] = data_val
        return self._extra_state_attributes

