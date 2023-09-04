"""Support for climate devices through the SmartThings cloud API."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
import logging
from typing import Any

from pysmartthings import Attribute, Capability

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DOMAIN as CLIMATE_DOMAIN,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartThingsEntity, SmartThingsEntity_custom
from .const import *
from .common import *

ATTR_OPERATION_STATE = "operation_state"
MODE_TO_STATE = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "eco": HVACMode.AUTO,
    "rush hour": HVACMode.AUTO,
    "emergency heat": HVACMode.HEAT,
    "heat": HVACMode.HEAT,
    "off": HVACMode.OFF,
}
STATE_TO_MODE = {
    HVACMode.HEAT_COOL: "auto",
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
    HVACMode.OFF: "off",
}

OPERATING_STATE_TO_ACTION = {
    "cooling": HVACAction.COOLING,
    "fan only": HVACAction.FAN,
    "heating": HVACAction.HEATING,
    "idle": HVACAction.IDLE,
    "pending cool": HVACAction.COOLING,
    "pending heat": HVACAction.HEATING,
    "vent economizer": HVACAction.FAN,
}

AC_MODE_TO_STATE = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "coolClean": HVACMode.COOL,
    "dryClean": HVACMode.DRY,
    "heat": HVACMode.HEAT,
    "heatClean": HVACMode.HEAT,
    "fanOnly": HVACMode.FAN_ONLY,
    "wind": HVACMode.FAN_ONLY,
}
STATE_TO_AC_MODE = {
    HVACMode.HEAT_COOL: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.HEAT: "heat",
    HVACMode.FAN_ONLY: "wind",
}

UNIT_MAP = {"C": UnitOfTemperature.CELSIUS, "F": UnitOfTemperature.FAHRENHEIT}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climate entities for a config entry."""
    ac_capabilities = [
        Capability.air_conditioner_mode,
        Capability.air_conditioner_fan_mode,
        Capability.switch,
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
    ]

    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    entities: list[ClimateEntity] = []
    if SettingManager.enable_default_entities():
        for device in broker.devices.values():
            if SettingManager.is_allow_device(device.device_id) == False:
                continue
            if not broker.any_assigned(device.device_id, CLIMATE_DOMAIN):
                continue
            if all(capability in device.capabilities for capability in ac_capabilities):
                entities.append(SmartThingsAirConditioner(device))
            else:
                entities.append(SmartThingsThermostat(device))

    custom_platform = CUSTOM_PLATFORMS[Platform.CLIMATE]
    for device_setting in SettingManager.get_device_setting():
        if device_setting["device_id"] in broker.devices:
            if custom_platform not in device_setting: 
                continue
        for device in broker.devices.values():
            # if SettingManager.is_allow_device(device.device_id) == False:
            #     continue
            if device.device_id == device_setting["device_id"]:
                for dev in device_setting[custom_platform]:
                    # _LOGGER.warning("device_id : %s => %s", device_setting["device_id"], dev)
                    climate = {
                        cap.get("capability"): cap for cap in dev.get("capabilities")
                    }
                    # _LOGGER.warning("climate_capabilities : %s", climate)
                    entities.append(
                        SmartThingsClimate_custom(
                            device,
                            dev.get("name"),
                            climate.get("switch"),
                            climate.get("airConditionerMode"),
                            climate.get("airConditionerFanMode"),
                            climate.get("thermostatCoolingSetpoint"),
                            climate.get("temperatureMeasurement")
                        )
                    )
    async_add_entities(entities, True)


class SmartThingsClimate_custom(SmartThingsEntity, ClimateEntity):
    """Define a SmartThings Air Conditioner."""
    def __init__(self, device, name:str, switch, airConditionerMode, airConditionerFanMode, thermostatCoolingSetpoint, temperatureMeasurement) -> None:
        super().__init__(device)
        self._hvac_modes = None
        self._device = device
        self._name = name
        self._switch = switch
        self._airConditionerMode = airConditionerMode
        self._airConditionerFanMode = airConditionerFanMode
        self._thermostatCoolingSetpoint = thermostatCoolingSetpoint
        self._temperatureMeasurement = temperatureMeasurement

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )

    @property
    def name(self) -> str:
        return f"{self._name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device.device_id}.{self._name}"

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        # """Set new target fan mode."""
        if self._airConditionerFanMode.get("component") == "main":
            await self._device.set_fan_mode(fan_mode, set_status=True)
            # State is set optimistically in the command above, therefore update
            # the entity state ahead of receiving the confirming push updates
        else:
            arg = []
            arg.append(fan_mode)
            await self._device.command(self._airConditionerFanMode.get("component"), self._airConditionerFanMode.get("capability"), self._airConditionerFanMode.get("commands")[0]["command"], arg)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        tasks = []
        # Turn on the device if it's off before setting mode.
        if self._switch.get("component") == "main":
            if not self._device.status.switch:
                tasks.append(self._device.switch_on(set_status=True))
            tasks.append(
                self._device.set_air_conditioner_mode(
                    STATE_TO_AC_MODE[hvac_mode], set_status=True
                )
            )
        else:
            value = self._device.status._components[self._switch.get("component")].attributes.get(self._switch.get("commands")[0]["attribute"]).value
            if not value in self._switch.get("commands")[0]["on_state"]:
                tasks.append(self._device.command(self._switch.get("component"), self._switch.get("capability"), self._switch.get("commands")[0]["on_command"], self._switch.get("commands")[0]["argument"]["on"]))
            arg = []
            arg.append(STATE_TO_AC_MODE[hvac_mode])
            tasks.append(
                self._device.command(self._airConditionerMode.get("component"), self._airConditionerMode.get("capability"), self._airConditionerMode.get("commands")[0]["command"], arg)
            )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        tasks = []
        # operation mode
        if operation_mode := kwargs.get(ATTR_HVAC_MODE):
            if self._switch.get("component") == "main":
                if operation_mode == HVACMode.OFF:
                    tasks.append(self._device.switch_off(set_status=True))
                else:
                    if not self._device.status.switch:
                        tasks.append(self._device.switch_on(set_status=True))
                    tasks.append(self.async_set_hvac_mode(operation_mode))
            else:
                if operation_mode == HVACMode.OFF:
                    tasks.append(self._device.command(self._switch.get("component"), self._switch.get("capability"), self._switch.get("commands")[0]["on_command"], self._switch.get("commands")[0]["argument"]["off"]))
                else:
                    value = self._device.status._components[self._switch.get("component")].attributes.get(self._switch.get("commands")[0]["attribute"]).value
                    if not value in self._switch.get("commands")[0]["on_state"]:
                        tasks.append(self._device.command(self._switch.get("component"), self._switch.get("capability"), self._switch.get("commands")[0]["on_command"], self._switch.get("commands")[0]["argument"]["on"]))
                    tasks.append(self.async_set_hvac_mode(operation_mode))
        # temperature
        if self._thermostatCoolingSetpoint.get("component") == "main":
            tasks.append(
                self._device.set_cooling_setpoint(kwargs[ATTR_TEMPERATURE], set_status=True)
            )
        else:
            arg = []
            arg.append(kwargs[ATTR_TEMPERATURE])
            tasks.append(
                self._device.command(self._thermostatCoolingSetpoint.get("component"), self._thermostatCoolingSetpoint.get("capability"), self._thermostatCoolingSetpoint.get("commands")[0]["command"], arg)
            )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn device on."""
        if self._switch.get("component") == "main":
            await self._device.switch_on(set_status=True)
        else:
            await self._device.command(self._switch.get("component"), self._switch.get("capability"), self._switch.get("commands")[0]["on_command"], self._switch.get("commands")[0]["argument"]["on"])
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn device off."""
        if self._switch.get("component") == "main":
            await self._device.switch_off(set_status=True)
        else:
            await self._device.command(self._switch.get("component"), self._switch.get("capability"), self._switch.get("commands")[0]["off_command"], self._switch.get("commands")[0]["argument"]["off"])
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the calculated fields of the AC."""
        modes = {HVACMode.OFF}
        if self._airConditionerMode.get("component") == "main":
            for mode in self._device.status.supported_ac_modes:
                if (state := AC_MODE_TO_STATE.get(mode)) is not None:
                    modes.add(state)
                else:
                    _LOGGER.debug(
                        "Device %s (%s) returned an invalid supported AC mode: %s",
                        self._device.label,
                        self._device.device_id,
                        mode,
                    )
        else:
            for mode in self._device.status._components[self._airConditionerMode.get("component")].attributes.get(self._airConditionerMode.get("options")["attribute"]).value:
                if (state := AC_MODE_TO_STATE.get(mode)) is not None:
                    modes.add(state)
                else:
                    _LOGGER.debug(
                        "Device %s (%s) returned an invalid supported AC mode: %s",
                        self._device.label,
                        self._device.device_id,
                        mode,
                    )
        self._hvac_modes = list(modes)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._temperatureMeasurement.get("component") == "main":
            return self._device.status.temperature
        else:
            return self._device.status._components[self._temperatureMeasurement.get("component")].attributes.get(self._temperatureMeasurement.get("attributes")[0]["attribute"]).value

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Include attributes from the Demand Response Load Control (drlc)
        and Power Consumption capabilities.
        """
        attributes = [
            "drlc_status_duration",
            "drlc_status_level",
            "drlc_status_start",
            "drlc_status_override",
        ]
        state_attributes = {}
        for attribute in attributes:
            value = getattr(self._device.status, attribute)
            if value is not None:
                state_attributes[attribute] = value
        state_attributes["min_temp"] = self._thermostatCoolingSetpoint.get("min")
        state_attributes["max_temp"] = self._thermostatCoolingSetpoint.get("max")
        state_attributes["target_temp_step"] = self._thermostatCoolingSetpoint.get("step")
        return state_attributes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        if self._airConditionerFanMode.get("component") == "main":
            return self._device.status.fan_mode
        else:
            return self._device.status._components[self._airConditionerFanMode.get("component")].attributes.get(self._airConditionerFanMode.get("commands")[0]["attribute"]).value

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self._airConditionerFanMode.get("component") == "main":
            return self._device.status.supported_ac_fan_modes
        else:
            return self._device.status._components[self._airConditionerFanMode.get("component")].attributes.get(self._airConditionerFanMode.get("options")["attribute"]).value

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation ie. heat, cool, idle."""
        if self._switch.get("component") == "main":
            if not self._device.status.switch:
                return HVACMode.OFF
            return AC_MODE_TO_STATE.get(self._device.status.air_conditioner_mode)
        else:
            value = self._device.status._components[self._switch.get("component")].attributes.get(self._switch.get("commands")[0]["attribute"]).value
            if not value in self._switch.get("commands")[0]["on_state"]:
                return HVACMode.OFF
            return AC_MODE_TO_STATE.get(self._device.status._components[self._airConditionerMode.get("component")].attributes.get(self._airConditionerMode.get("commands")[0]["attribute"]).value)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._thermostatCoolingSetpoint.get("component") == "main":
            return self._device.status.cooling_setpoint
        else:
            return self._device.status._components[self._thermostatCoolingSetpoint.get("component")].attributes.get(self._thermostatCoolingSetpoint.get("commands")[0]["attribute"]).value

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._thermostatCoolingSetpoint.get("component") == "main":
            return UNIT_MAP.get(self._device.status.attributes[Attribute.temperature].unit)
        else:
            return UNIT_MAP.get(self._device.status._components[self._temperatureMeasurement.get("component")].attributes[Attribute.temperature].unit)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""
    supported = [
        Capability.air_conditioner_mode,
        Capability.demand_response_load_control,
        Capability.air_conditioner_fan_mode,
        Capability.switch,
        Capability.thermostat,
        Capability.thermostat_cooling_setpoint,
        Capability.thermostat_fan_mode,
        Capability.thermostat_heating_setpoint,
        Capability.thermostat_mode,
        Capability.thermostat_operating_state,
    ]
    # Can have this legacy/deprecated capability
    if Capability.thermostat in capabilities:
        return supported
    # Or must have all of these thermostat capabilities
    thermostat_capabilities = [
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
        Capability.thermostat_heating_setpoint,
        Capability.thermostat_mode,
    ]
    if all(capability in capabilities for capability in thermostat_capabilities):
        return supported
    # Or must have all of these A/C capabilities
    ac_capabilities = [
        Capability.air_conditioner_mode,
        Capability.air_conditioner_fan_mode,
        Capability.switch,
        Capability.temperature_measurement,
        Capability.thermostat_cooling_setpoint,
    ]
    if all(capability in capabilities for capability in ac_capabilities):
        return supported
    return None


class SmartThingsThermostat(SmartThingsEntity, ClimateEntity):
    """Define a SmartThings climate entities."""

    def __init__(self, device):
        """Init the class."""
        super().__init__(device)
        self._attr_supported_features = self._determine_features()
        self._hvac_mode = None
        self._hvac_modes = None

    def _determine_features(self):
        flags = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        if self._device.get_capability(
            Capability.thermostat_fan_mode, Capability.thermostat
        ):
            flags |= ClimateEntityFeature.FAN_MODE
        return flags

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._device.set_thermostat_fan_mode(fan_mode, set_status=True)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target operation mode."""
        mode = STATE_TO_MODE[hvac_mode]
        await self._device.set_thermostat_mode(mode, set_status=True)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new operation mode and target temperatures."""
        # Operation state
        if operation_state := kwargs.get(ATTR_HVAC_MODE):
            mode = STATE_TO_MODE[operation_state]
            await self._device.set_thermostat_mode(mode, set_status=True)
            await self.async_update()

        # Heat/cool setpoint
        heating_setpoint = None
        cooling_setpoint = None
        if self.hvac_mode == HVACMode.HEAT:
            heating_setpoint = kwargs.get(ATTR_TEMPERATURE)
        elif self.hvac_mode == HVACMode.COOL:
            cooling_setpoint = kwargs.get(ATTR_TEMPERATURE)
        else:
            heating_setpoint = kwargs.get(ATTR_TARGET_TEMP_LOW)
            cooling_setpoint = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        tasks = []
        if heating_setpoint is not None:
            tasks.append(
                self._device.set_heating_setpoint(
                    round(heating_setpoint, 3), set_status=True
                )
            )
        if cooling_setpoint is not None:
            tasks.append(
                self._device.set_cooling_setpoint(
                    round(cooling_setpoint, 3), set_status=True
                )
            )
        await asyncio.gather(*tasks)

        # State is set optimistically in the commands above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Update the attributes of the climate device."""
        thermostat_mode = self._device.status.thermostat_mode
        self._hvac_mode = MODE_TO_STATE.get(thermostat_mode)
        if self._hvac_mode is None:
            _LOGGER.debug(
                "Device %s (%s) returned an invalid hvac mode: %s",
                self._device.label,
                self._device.device_id,
                thermostat_mode,
            )

        modes = set()
        supported_modes = self._device.status.supported_thermostat_modes
        if isinstance(supported_modes, Iterable):
            for mode in supported_modes:
                if (state := MODE_TO_STATE.get(mode)) is not None:
                    modes.add(state)
                else:
                    _LOGGER.debug(
                        (
                            "Device %s (%s) returned an invalid supported thermostat"
                            " mode: %s"
                        ),
                        self._device.label,
                        self._device.device_id,
                        mode,
                    )
        else:
            _LOGGER.debug(
                "Device %s (%s) returned invalid supported thermostat modes: %s",
                self._device.label,
                self._device.device_id,
                supported_modes,
            )
        self._hvac_modes = list(modes)

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._device.status.humidity

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.status.temperature

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._device.status.thermostat_fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._device.status.supported_thermostat_fan_modes

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        return OPERATING_STATE_TO_ACTION.get(
            self._device.status.thermostat_operating_state
        )

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation ie. heat, cool, idle."""
        return self._hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVACMode.COOL:
            return self._device.status.cooling_setpoint
        if self.hvac_mode == HVACMode.HEAT:
            return self._device.status.heating_setpoint
        return None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._device.status.cooling_setpoint
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return self._device.status.heating_setpoint
        return None

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UNIT_MAP.get(self._device.status.attributes[Attribute.temperature].unit)


class SmartThingsAirConditioner(SmartThingsEntity, ClimateEntity):
    """Define a SmartThings Air Conditioner."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )

    def __init__(self, device):
        """Init the class."""
        super().__init__(device)
        self._hvac_modes = None

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._device.set_fan_mode(fan_mode, set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        tasks = []
        # Turn on the device if it's off before setting mode.
        if not self._device.status.switch:
            tasks.append(self._device.switch_on(set_status=True))
        tasks.append(
            self._device.set_air_conditioner_mode(
                STATE_TO_AC_MODE[hvac_mode], set_status=True
            )
        )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        tasks = []
        # operation mode
        if operation_mode := kwargs.get(ATTR_HVAC_MODE):
            if operation_mode == HVACMode.OFF:
                tasks.append(self._device.switch_off(set_status=True))
            else:
                if not self._device.status.switch:
                    tasks.append(self._device.switch_on(set_status=True))
                tasks.append(self.async_set_hvac_mode(operation_mode))
        # temperature
        tasks.append(
            self._device.set_cooling_setpoint(kwargs[ATTR_TEMPERATURE], set_status=True)
        )
        await asyncio.gather(*tasks)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn device on."""
        await self._device.switch_on(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn device off."""
        await self._device.switch_off(set_status=True)
        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the calculated fields of the AC."""
        modes = {HVACMode.OFF}
        for mode in self._device.status.supported_ac_modes:
            if (state := AC_MODE_TO_STATE.get(mode)) is not None:
                modes.add(state)
            else:
                _LOGGER.debug(
                    "Device %s (%s) returned an invalid supported AC mode: %s",
                    self._device.label,
                    self._device.device_id,
                    mode,
                )
        self._hvac_modes = list(modes)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._device.status.temperature

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Include attributes from the Demand Response Load Control (drlc)
        and Power Consumption capabilities.
        """
        attributes = [
            "drlc_status_duration",
            "drlc_status_level",
            "drlc_status_start",
            "drlc_status_override",
        ]
        state_attributes = {}
        for attribute in attributes:
            value = getattr(self._device.status, attribute)
            if value is not None:
                state_attributes[attribute] = value
        return state_attributes

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._device.status.fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._device.status.supported_ac_fan_modes

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation ie. heat, cool, idle."""
        if not self._device.status.switch:
            return HVACMode.OFF
        return AC_MODE_TO_STATE.get(self._device.status.air_conditioner_mode)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        return self._hvac_modes

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._device.status.cooling_setpoint

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UNIT_MAP.get(self._device.status.attributes[Attribute.temperature].unit)
