"""Support for SmartThings Cloud Customize."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from http import HTTPStatus
import importlib
import logging
from typing import TYPE_CHECKING, Any

import homeassistant
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from pysmartthings import SmartThings

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_send,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_loaded_integration
from homeassistant.setup import SetupPhases, async_pause_setup
from homeassistant import config_entries, core

from .common import SettingManager
from .config_flow import SmartThingsFlowHandler  # noqa: F401
from .const import (
    CONF_LOCATION_ID,
    CONF_TOKEN,
    CONF_RESETTING_ENTITIES,
    CONF_ENABLE_SYNTAX_PROPERTY,
    DATA_BROKERS,
    DOMAIN,
    EVENT_BUTTON,
    PLATFORMS,
    SIGNAL_SMARTTHINGS_UPDATE,
)

from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Initialize the SmartThings Customize platform."""
    hass.data.setdefault(DOMAIN, {DATA_BROKERS: {}, "listener": []})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of a previous version config entry."""
    if entry.version < 3:
        # Old PAT-based entries need reauthentication
        _LOGGER.info(
            "Migrating SmartThings Customize entry from version %s to 3",
            entry.version
        )
        hass.config_entries.async_update_entry(
            entry,
            version=3,
            minor_version=1,
        )
        raise ConfigEntryAuthFailed("Config entry requires reauthentication for OAuth2")
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize config entry which represents an installed SmartApp."""
    entry.update_listeners.clear()
    
    # Ensure we have the new OAuth2 token format
    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed("Config entry missing token - please reauthenticate")
    
    # Use original SmartThings OAuth implementation
    from homeassistant.helpers.config_entry_oauth2_flow import async_get_implementations
    SMARTTHINGS_DOMAIN = "smartthings"
    
    try:
        implementations = await async_get_implementations(hass, SMARTTHINGS_DOMAIN)
        if not implementations:
            raise ImplementationUnavailableError("No OAuth implementation available")
        
        # Get the implementation that was used (stored in entry.data)
        impl_key = entry.data.get("auth_implementation")
        if impl_key and impl_key in implementations:
            implementation = implementations[impl_key]
        else:
            # Use the first available implementation
            implementation = list(implementations.values())[0]
            
    except Exception as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err
    
    session = OAuth2Session(hass, entry, implementation)
    
    try:
        await session.async_ensure_token_valid()
    except ClientResponseError as err:
        if err.status == HTTPStatus.BAD_REQUEST:
            raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from err
        raise ConfigEntryNotReady from err

    client = SmartThings(session=async_get_clientsession(hass))
    
    async def _refresh_token() -> str:
        await session.async_ensure_token_valid()
        token = session.token[CONF_ACCESS_TOKEN]
        if TYPE_CHECKING:
            assert isinstance(token, str)
        return token
    
    client.refresh_token_function = _refresh_token
    
    # Ensure platform modules are loaded
    await async_get_loaded_integration(hass, DOMAIN).async_get_platforms(PLATFORMS)
    
    # Initialize settings
    location = await client.get_location(entry.data[CONF_LOCATION_ID])
    settings = SettingManager()
    settings.init(hass, location)
    await hass.async_add_executor_job(settings.load_setting)
    settings.set_options(entry.options)
    
    try:
        # Get devices
        devices = await client.get_devices()
        location_devices = [
            d for d in devices 
            if hasattr(d, 'location_id') and d.location_id == entry.data[CONF_LOCATION_ID]
        ]
        
        # Get device status
        device_status = {}
        for device in location_devices:
            try:
                status = await client.get_device_status(device.device_id)
                device_status[device.device_id] = {
                    "device": device,
                    "status": status,
                }
            except ClientResponseError:
                _LOGGER.debug(
                    "Unable to update status for device: %s (%s), the device will be excluded",
                    device.label,
                    device.device_id,
                    exc_info=True,
                )
        
        # Get scenes
        scenes = await client.get_scenes(location_id=entry.data[CONF_LOCATION_ID])
        
        # Setup device broker
        with async_pause_setup(hass, SetupPhases.WAIT_IMPORT_PLATFORMS):
            broker = await hass.async_add_import_executor_job(
                DeviceBroker, hass, entry, client, session, device_status, scenes
            )
        
        hass.data[DOMAIN][DATA_BROKERS][entry.entry_id] = broker
        
    except ClientResponseError as ex:
        if ex.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise ConfigEntryAuthFailed(
                f"Unable to setup configuration entry '{entry.title}' - please reconfigure"
            ) from ex
        raise ConfigEntryNotReady from ex
    except (ClientConnectionError, RuntimeWarning) as ex:
        raise ConfigEntryNotReady from ex
    
    # Handle entity reset option
    if SettingManager.resetting_entities():
        entity_registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        for e in entities:
            entity_registry.async_remove(e.entity_id)
        
        device_registry = dr.async_get(hass)
        device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        for d in device_entries:
            device_registry.async_update_device(d.id, remove_config_entry_id=entry.entry_id)
    
    # Update options to reset the resetting flag
    hass.config_entries.async_update_entry(
        entry,
        options={
            CONF_ENABLE_SYNTAX_PROPERTY: entry.options.get(CONF_ENABLE_SYNTAX_PROPERTY, False),
            CONF_RESETTING_ENTITIES: False,
        }
    )
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    _LOGGER.debug("Enable platforms: %s", SettingManager().get_enable_platforms())
    await hass.config_entries.async_forward_entry_setups(entry, SettingManager().get_enable_platforms())
    
    return True


async def update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for listener in hass.data[DOMAIN].get("listener", []):
        listener()
    
    broker = hass.data[DOMAIN][DATA_BROKERS].pop(entry.entry_id, None)
    if broker:
        broker.disconnect()
    
    return await hass.config_entries.async_unload_platforms(
        entry, SettingManager().get_enable_platforms()
    )


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Perform clean-up when entry is being removed."""
    # With OAuth2, we don't have a SmartApp to clean up
    _LOGGER.debug("Removed SmartThings Customize entry: %s", entry.title)


class DeviceBroker:
    """Manages an individual SmartThings Customize config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: SmartThings,
        session: OAuth2Session,
        device_status: dict,
        scenes: Iterable,
    ) -> None:
        """Create a new instance of the DeviceBroker."""
        self._hass = hass
        self._entry = entry
        self._client = client
        self._session = session
        self._disconnect_callbacks = []
        
        # Build device and scene dictionaries
        self.devices = {}
        for device_id, data in device_status.items():
            self.devices[device_id] = data["device"]
        
        self.device_status = device_status
        self.scenes = {scene.scene_id: scene for scene in scenes}
        self._created_entities = []
        
        # Assign capabilities to platforms
        self._assignments = self._assign_capabilities(list(self.devices.values()))

    def add_valid_entity(self, entity_id):
        """Track a created entity."""
        self._created_entities.append(entity_id)

    def is_valid_entity(self, entity_id):
        """Check if entity was created."""
        return entity_id in self._created_entities

    def _assign_capabilities(self, devices: Iterable):
        """Assign platforms to capabilities."""
        assignments = {}
        for device in devices:
            capabilities = list(device.capabilities) if hasattr(device, 'capabilities') else []
            slots = {}
            for platform in PLATFORMS:
                platform_module = importlib.import_module(f".{platform}", self.__module__)
                if not hasattr(platform_module, "get_capabilities"):
                    continue
                assigned = platform_module.get_capabilities(capabilities.copy())
                if not assigned:
                    continue
                for capability in assigned:
                    if capability not in capabilities:
                        continue
                    capabilities.remove(capability)
                    slots[capability] = platform
            assignments[device.device_id] = slots
        return assignments

    def connect(self):
        """Connect handlers/listeners for device/lifecycle events."""
        # OAuth2 uses different subscription mechanism
        # For now, we'll rely on polling or SSE if available
        pass

    def disconnect(self):
        """Disconnect handlers/listeners for device/lifecycle events."""
        for callback in self._disconnect_callbacks:
            callback()
        self._disconnect_callbacks.clear()

    def get_assigned(self, device_id: str, platform: str):
        """Get the capabilities assigned to the platform."""
        slots = self._assignments.get(device_id, {})
        return [key for key, value in slots.items() if value == platform]

    def any_assigned(self, device_id: str, platform: str):
        """Return True if the platform has any assigned capabilities."""
        slots = self._assignments.get(device_id, {})
        return any(value for value in slots.values() if value == platform)
