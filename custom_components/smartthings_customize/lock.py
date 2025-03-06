"""Support for locks through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .pysmartthings import Attribute, Capability

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import *

import logging
_LOGGER = logging.getLogger(__name__)


ST_STATE_LOCKED = "locked"
ST_LOCK_ATTR_MAP = {
    "codeId": "code_id",
    "codeName": "code_name",
    "lockName": "lock_name",
    "method": "method",
    "timeout": "timeout",
    "usedCode": "used_code",
}

from .lock_custom import SmartThingsLock_custom

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add locks for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    entities = []
    if SettingManager.enable_default_entities():
        async_add_entities(
            [
                SmartThingsLock(device)
                for device in broker.devices.values()
                if broker.any_assigned(device.device_id, "lock") and SettingManager.allow_device(device.device_id)
            ]
        )

    settings = SettingManager.get_capa_settings(broker, Platform.LOCK)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsLock_custom(hass=hass, setting=s))

    async_add_entities(entities)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    if Capability.lock in capabilities:
        return [Capability.lock]
    return None


class SmartThingsLock(SmartThingsEntity, LockEntity):
    """Define a SmartThings lock."""

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        await self._device.lock(set_status=True)
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        await self._device.unlock(set_status=True)
        self.async_write_ha_state()

    @property
    def is_locked(self) -> bool:
        """Return true if lock is locked."""
        return self._device.status.lock == ST_STATE_LOCKED

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        state_attrs = {}
        status = self._device.status.attributes[Attribute.lock]
        if status.value:
            state_attrs["lock_state"] = status.value
        if isinstance(status.data, dict):
            for st_attr, ha_attr in ST_LOCK_ATTR_MAP.items():
                if (data_val := status.data.get(st_attr)) is not None:
                    state_attrs[ha_attr] = data_val
        return state_attrs