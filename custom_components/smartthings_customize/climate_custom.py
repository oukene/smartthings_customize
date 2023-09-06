from . import SmartThingsEntity, SmartThingsEntity_custom
from homeassistant.components.climate import *

from homeassistant.helpers.event import async_track_state_change

from .const import *
from .common import *

from homeassistant.const import *
import asyncio
import logging
_LOGGER = logging.getLogger(__name__)

ATTR_SWITCH = "switch"
ATTR_MODE = "mode"
ATTR_TARGET_TEMP = "target_temp"
ATTR_TARGET_HUM = "target_humidity"

class SmartThingsClimate_custom(SmartThingsEntity_custom, ClimateEntity, ExtraCapability):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("climate settings : " + str(setting[2]))

        self._supported_features = 0
        self._extra_capability = {}
         self._hvac_modes = []

        for capa in setting[2]["capabilities"]:
            if ATTR_SWITCH in capa:
                self._extra_capability[ATTR_SWITCH] = capa
            elif ATTR_MODE in capa:
                self._extra_capability[ATTR_MODE] = capa
            elif ATTR_FAN_MODE in capa:
                self._extra_capability[ATTR_FAN_MODE] = capa
                self._supported_features |= ClimateEntityFeature.FAN_MODE
            elif ATTR_TARGET_TEMP in capa:
                self._extra_capability[ATTR_TARGET_TEMP] = capa
                self._supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            elif ATTR_TARGET_TEMP_LOW in capa:
                self._extra_capability[ATTR_TARGET_TEMP_LOW] = capa
            elif ATTR_TARGET_TEMP_HIGH in capa:
                self._extra_capability[ATTR_TARGET_TEMP_HIGH] = capa
            elif ATTR_TARGET_HUM in capa:
                self._extra_capability[ATTR_TARGET_HUM] = capa
                self._supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
            elif ATTR_CURRENT_TEMPERATURE in capa:
                self._extra_capability[ATTR_CURRENT_TEMPERATURE] = capa
            elif ATTR_CURRENT_HUMIDITY in capa:
                self._extra_capability[ATTR_CURRENT_HUMIDITY] = capa
            elif ATTR_PRESET_MODE in capa:
                self._extra_capability[ATTR_PRESET_MODE] = capa
                self._supported_features |= ClimateEntityFeature.PRESET_MODE
            elif ATTR_SWING_MODE in capa:
                self._extra_capability[ATTR_SWING_MODE] = capa
                self._supported_features |= ClimateEntityFeature.SWING_MODE

        if self.get_extra_capa_attr_value(ATTR_MODE, "aux_heat_modes"):
            self._supported_features |= ClimateEntityFeature.AUX_HEAT

        if self._extra_capability.get(ATTR_TARGET_TEMP_HIGH) and self._extra_capability.get(ATTR_TARGET_TEMP_LOW):
            self._supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

        # external_entity
        if self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id"):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id"), self.entity_listener))

        if self.get_extra_capa_attr_value(ATTR_CURRENT_TEMPERATURE, "entity_id"):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, self.get_extra_capa_attr_value(ATTR_CURRENT_TEMPERATURE, "entity_id"), self.entity_listener))

        if self.get_extra_capa_attr_value(ATTR_CURRENT_HUMIDITY, "entity_id"):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, self.get_extra_capa_attr_value(ATTR_CURRENT_HUMIDITY, "entity_id"), self.entity_listener))

        # convert hvac_modes
        modes = ["off"]
        modes.extend(self.get_extra_capa_attr_value(ATTR_MODE, "options"))
        modes = list(set(modes))
        hvac_modes = self.get_extra_capa_attr_value(ATTR_MODE, "hvac_modes", [{}])
        for mode in modes:
            self._hvac_modes.append(hvac_modes[0].get(mode, mode))
                
        
    def entity_listener(self, entity, old_state, new_state):
        self.schedule_update_ha_state(True)

    # platform property #############################################################################
    @property
    def is_on(self) -> bool:
        entity_id = self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id")
        if entity_id:
            if self.hass.states.get(entity_id).state == "off":
                return False
        if get_attribute_value(self._device, self._component, ATTR_SWITCH, ATTR_SWITCH) == "off":
            return False
        return True

    @property
    def temperature_unit(self) -> str:
        return self.hass.config.units.temperature_unit

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        if hasattr(self, "_attr_precision"):
            return self._attr_precision
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return PRECISION_TENTHS
        return PRECISION_WHOLE

    @property
    def supported_features(self) -> int | None:
        return self._supported_features

    @property
    def hvac_mode(self):
        if not self.is_on:
            return HVACMode.OFF
        mode = self.get_extra_capa_attr_value(ATTR_MODE, "commands")
        hvac_modes = self.get_extra_capa_attr_value(ATTR_MODE, "hvac_modes", [{}])
        _LOGGER.debug("mode: " + str(mode) + ", hvac_modes : " + str(hvac_modes[0]))
        return hvac_modes[0].get(mode, mode)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return self._hvac_modes

    @property
    def fan_mode(self) -> str | None:
        return self.get_extra_capa_attr_value(ATTR_FAN_MODE, "commands")
    
    @property
    def fan_modes(self) -> list[str] | None:
        return self.get_extra_capa_attr_value(ATTR_FAN_MODE, "options")

    @property
    def target_temperature(self) -> float | None:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP, "commands")

    @property
    def target_temperature_high(self) -> float | None:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP_HIGH, "commands")

    @property
    def target_temperature_low(self) -> float | None:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP_LOW, "commands")


    @property
    def target_temperature_step(self) -> float | None:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP, "step")

    @property
    def current_temperature(self) -> float | None:
        # external temperature entity
        entity_id = self.get_extra_capa_attr_value(ATTR_CURRENT_TEMPERATURE, "entity_id")
        if entity_id:
            state = self.hass.states.get(entity_id)
            return float(state.state)
        else:
            return self.get_extra_capa_attr_value(ATTR_CURRENT_TEMPERATURE, "attributes")
            
    @property
    def max_temp(self) -> float:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP, "max")

    @property
    def min_temp(self) -> float:
        return self.get_extra_capa_attr_value(ATTR_TARGET_TEMP, "min")

    @property
    def current_humidity(self) -> int | None:
        # external humidity entity
        entity_id = self.get_extra_capa_attr_value(ATTR_CURRENT_HUMIDITY, "entity_id")
        if entity_id:
            state = self.hass.states.get(entity_id)
            return int(float(state.state))
        else:
            return int(float(self.get_extra_capa_attr_value(ATTR_CURRENT_HUMIDITY, "attributes")))
            
    @property
    def target_humidity(self) -> int | None:
        return int(float(self.get_extra_capa_attr_value(ATTR_TARGET_HUM, "commands")))

    @property
    def max_humidity(self) -> int:
        return int(float(self.get_extra_capa_attr_value(ATTR_TARGET_HUM, "max")))

    @property
    def min_humidity(self) -> int:
        return int(float(self.get_extra_capa_attr_value(ATTR_TARGET_HUM, "min")))
    
    @property
    def preset_mode(self) -> str | None:
        return self.get_extra_capa_attr_value(ATTR_PRESET_MODE, "commands")

    @property
    def preset_modes(self) -> list[str] | None:
        return self.get_extra_capa_attr_value(ATTR_PRESET_MODE, "options")

    @property
    def swing_mode(self) -> str | None:
        return self.get_extra_capa_attr_value(ATTR_SWING_MODE, "commands")

    @property
    def swing_modes(self) -> list[str] | None:
        return self.get_extra_capa_attr_value(ATTR_SWING_MODE, "options")

    @property
    def hvac_action(self) -> HVACAction | None:
        mode = self.get_extra_capa_attr_value(ATTR_MODE, "commands")
        actions = self.get_extra_capa_attr_value(ATTR_MODE, "hvac_actions", [{}])
        return actions[0].get(mode, None)
        
    @property
    def is_aux_heat(self) -> bool | None:
        mode = self.get_extra_capa_attr_value(ATTR_MODE, "commands")
        aux_heat_modes = self.get_extra_capa_attr_value(ATTR_MODE, "aux_heat_modes")
        return mode in (aux_heat_modes)
    

    # # method ########################################################################################
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._device.command(self._component, ATTR_SWITCH, "off")
            return
        tasks = []
        hvac_modes = self.get_extra_capa_attr_value(ATTR_MODE, "hvac_modes", [{}])
        mode = hvac_mode
        for k, v in hvac_modes[0].items():
            if v == hvac_mode:
                mode = k
                break
        if not self.is_on:
            tasks.append(self._device.command(self._component, ATTR_SWITCH, "on"))
        tasks.append(
            self._device.command(self._component, self.get_extra_capa_capability(ATTR_MODE), self.get_extra_capa_command(ATTR_MODE), [mode])
        )
        await asyncio.gather(*tasks)
        self.async_write_ha_state()
    
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._device.command(
            self._component, self.get_extra_capa_capability(ATTR_PRESET_MODE), self.get_extra_capa_command(ATTR_PRESET_MODE), [preset_mode])

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._device.command(
            self._component, self.get_extra_capa_capability(ATTR_FAN_MODE), self.get_extra_capa_command(ATTR_FAN_MODE), [fan_mode])

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._device.command(
            self._component, self.get_extra_capa_capability(ATTR_SWING_MODE), self.get_extra_capa_command(ATTR_SWING_MODE), [swing_mode])
        
    async def async_set_humidity(self, humidity: int) -> None:
        await self._device.command(
            self._component, self.get_extra_capa_capability(ATTR_TARGET_HUM), self.get_extra_capa_command(ATTR_TARGET_HUM), [humidity])

    async def async_set_temperature(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if key != "entity_id":
                await self._device.command(self._component, self.get_extra_capa_capability(key), self.get_extra_capa_command(key), [kwargs[key]])

    async def async_turn_on(self) -> None:
        await self._device.command(self._component, ATTR_SWITCH, "on")
        
    async def async_turn_off(self) -> None:
        await self._device.command(self._component, ATTR_SWITCH, "off")
    
    # async def async_turn_aux_heat_off(self) -> None:
    #     await self._device.command(self._component, self.get_extra_capa_capability(ATTR_AUX_HEAT), self.get_extra_capa_attr_value(ATTR_AUX_HEAT, "off_command"))

    # async def async_turn_aux_heat_on(self) -> None:
    #     return await super().async_turn_aux_heat_on()
