"""Support for SmartThings Cloud Customize with OAuth2."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from http import HTTPStatus
import importlib
import logging

import homeassistant
from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from .pysmartapp.event import EVENT_TYPE_DEVICE
from .pysmartthings import Attribute, Capability, SmartThings

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_implementations,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.loader import async_get_loaded_integration
from homeassistant.setup import SetupPhases, async_pause_setup

from .common import *
from .device import SmartThings_custom

from homeassistant import config_entries, core

from .config_flow import SmartThingsFlowHandler  # noqa: F401
from .const import *

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

# Original SmartThings domain for OAuth credentials
SMARTTHINGS_DOMAIN = "smartthings"

# Token refresh interval (12 hours)
TOKEN_REFRESH_INTERVAL = timedelta(hours=12)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Initialize the SmartThings Customize platform."""
    hass.data.setdefault(DOMAIN, {DATA_BROKERS: {}, "listener": []})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of a previous version config entry."""
    if entry.version < 3:
        _LOGGER.info(
            "Migrating SmartThings Customize entry from version %s to 3 - reconfiguration required",
            entry.version
        )
        raise ConfigEntryAuthFailed("Config entry requires reconfiguration for OAuth2")
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize config entry with OAuth2 authentication."""
    entry.update_listeners.clear()
    
    # Ensure we have the OAuth2 token
    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed("Config entry missing token - please reconfigure")
    
    # Get OAuth implementation from original SmartThings domain
    try:
        implementations = await async_get_implementations(hass, SMARTTHINGS_DOMAIN)
        if not implementations:
            raise ConfigEntryNotReady("No OAuth implementation available")
        
        # Use the first available implementation
        implementation = list(implementations.values())[0]
    except Exception as err:
        _LOGGER.error("Failed to get OAuth implementation: %s", err)
        raise ConfigEntryNotReady("OAuth implementation unavailable") from err
    
    session = OAuth2Session(hass, entry, implementation)
    
    try:
        await session.async_ensure_token_valid()
    except ClientResponseError as err:
        if err.status == HTTPStatus.BAD_REQUEST:
            raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from err
        raise ConfigEntryNotReady from err
    
    # Get current access token
    access_token = session.token[CONF_ACCESS_TOKEN]
    
    # Create API client with OAuth2 token
    api = SmartThings_custom(async_get_clientsession(hass), access_token)
    
    # Ensure platform modules are loaded
    await async_get_loaded_integration(hass, DOMAIN).async_get_platforms(PLATFORMS)
    
    # Initialize settings
    location_id = entry.data[CONF_LOCATION_ID]
    settings = SettingManager()
    settings.init(hass, await api.location(location_id))
    await hass.async_add_executor_job(settings.load_setting)
    SettingManager().set_options(entry.options)
    
    try:
        # Get devices and their current status
        devices = await api.devices(location_ids=[location_id])
        
        async def retrieve_device_status(device):
            try:
                await device.status.refresh()
            except ClientResponseError:
                _LOGGER.debug(
                    "Unable to update status for device: %s (%s), the device will be excluded",
                    device.label,
                    device.device_id,
                    exc_info=True,
                )
                devices.remove(device)
        
        await asyncio.gather(*(retrieve_device_status(d) for d in devices.copy()))
        
        # Get scenes
        scenes = await async_get_entry_scenes(entry, api)
        
        # Setup device broker with OAuth2 session
        with async_pause_setup(hass, SetupPhases.WAIT_IMPORT_PLATFORMS):
            broker = await hass.async_add_import_executor_job(
                DeviceBroker, hass, entry, session, devices, scenes
            )
        broker.connect()
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
    
    hass.config_entries.async_update_entry(
        entry,
        options={
            CONF_ENABLE_SYNTAX_PROPERTY: entry.options.get(CONF_ENABLE_SYNTAX_PROPERTY, False),
            CONF_RESETTING_ENTITIES: False,
        }
    )
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    hass.data[DOMAIN]["listener"] = []
    _LOGGER.debug("Enable platforms: %s", SettingManager().get_enable_platforms())
    await hass.config_entries.async_forward_entry_setups(entry, SettingManager().get_enable_platforms())
    return True


async def update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    config_entry.update_listeners.clear()
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_get_entry_scenes(entry: ConfigEntry, api):
    """Get the scenes within an integration."""
    try:
        return await api.scenes(location_id=entry.data[CONF_LOCATION_ID])
    except ClientResponseError as ex:
        if ex.status == HTTPStatus.FORBIDDEN:
            _LOGGER.exception(
                "Unable to load scenes for configuration entry '%s' because the access token does not have the required access",
                entry.title,
            )
        else:
            raise
    return []


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for listener in hass.data[DOMAIN].get("listener", []):
        listener()
    
    broker = hass.data[DOMAIN][DATA_BROKERS].pop(entry.entry_id, None)
    if broker:
        broker.disconnect()
    
    return await hass.config_entries.async_unload_platforms(entry, SettingManager().get_enable_platforms())


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Perform clean-up when entry is being removed."""
    _LOGGER.debug("Removed SmartThings Customize entry: %s", entry.title)


class DeviceBroker:
    """Manages an individual SmartThings Customize config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: OAuth2Session,
        devices: Iterable,
        scenes: Iterable,
    ) -> None:
        """Create a new instance of the DeviceBroker."""
        self._hass = hass
        self._entry = entry
        self._session = session
        self._token_refresh_remove = None
        self._assignments = self._assign_capabilities(devices)
        self.devices = {device.device_id: device for device in devices}
        self.scenes = {scene.scene_id: scene for scene in scenes}
        self._created_entities = []

    def add_valid_entity(self, entity_id):
        """Track created entity."""
        self._created_entities.append(entity_id)

    def is_valid_entity(self, entity_id):
        """Check if entity was created."""
        return entity_id in self._created_entities

    def build_capability(self, device) -> dict:
        """Build capability dictionary for device."""
        capabilities = {}
        capabilities["main"] = device.capabilities
        for key, value in device.components.items():
            capabilities[key] = value
        return capabilities

    def _assign_capabilities(self, devices: Iterable):
        """Assign platforms to capabilities."""
        assignments = {}
        for device in devices:
            capabilities = device.capabilities.copy()
            slots = {}
            for platform in PLATFORMS:
                platform_module = importlib.import_module(
                    f".{platform}", self.__module__
                )
                if not hasattr(platform_module, "get_capabilities"):
                    continue
                assigned = platform_module.get_capabilities(capabilities)
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
        """Connect handlers/listeners for token refresh."""
        
        async def refresh_token_and_update(now):
            """Refresh OAuth2 token and update device API tokens."""
            try:
                await self._session.async_ensure_token_valid()
                new_token = self._session.token[CONF_ACCESS_TOKEN]
                
                # Update all device API tokens
                for device in self.devices.values():
                    if hasattr(device, 'status') and hasattr(device.status, '_api'):
                        device.status._api._token = new_token
                
                _LOGGER.debug("Refreshed OAuth2 token for entry: %s", self._entry.title)
            except Exception as err:
                _LOGGER.error("Failed to refresh OAuth2 token: %s", err)
        
        self._token_refresh_remove = async_track_time_interval(
            self._hass, refresh_token_and_update, TOKEN_REFRESH_INTERVAL
        )

    def disconnect(self):
        """Disconnect handlers/listeners."""
        if self._token_refresh_remove:
            self._token_refresh_remove()

    def get_assigned(self, device_id: str, platform: str):
        """Get the capabilities assigned to the platform."""
        slots = self._assignments.get(device_id, {})
        return [key for key, value in slots.items() if value == platform]

    def any_assigned(self, device_id: str, platform: str):
        """Return True if the platform has any assigned capabilities."""
        slots = self._assignments.get(device_id, {})
        return any(value for value in slots.values() if value == platform)


class SmartThingsEntity(Entity):
    """Defines a SmartThings entity."""

    _attr_should_poll = False

    def __init__(self, device) -> None:
        """Initialize the instance."""
        self._device = device
        self._dispatcher_remove = None

    async def async_added_to_hass(self):
        """Device added to hass."""

        async def async_update_state(devices, evt=None):
            """Update device state."""
            if self._device.device_id in devices:
                self.async_write_ha_state()

        self._dispatcher_remove = async_dispatcher_connect(
            self.hass, SIGNAL_SMARTTHINGS_UPDATE, async_update_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect the device when removed."""
        if self._dispatcher_remove:
            self._dispatcher_remove()

    @property
    def device_info(self) -> DeviceInfo:
        """Get attributes about the device."""
        return DeviceInfo(
            configuration_url="https://account.smartthings.com",
            identifiers={(DOMAIN, self._device.device_id)},
            manufacturer=self._device.status.ocf_manufacturer_name,
            model=self._device.status.ocf_model_number,
            name=self._device.label,
            hw_version=self._device.status.ocf_hardware_version,
            sw_version=self._device.status.ocf_firmware_version,
        )

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device.label

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._device.device_id
