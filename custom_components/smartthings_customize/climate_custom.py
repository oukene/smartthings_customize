from . import SmartThingsEntity
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

class SmartThingsClimate_custom(SmartThingsEntity_custom, ClimateEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("climate settings : " + str(setting[1]))

        self._supported_features = 0
        self._hvac_modes = []
        self._fan_modes = []
        
        for capa in setting[1].get("capabilities", []):
            if ATTR_SWITCH in capa:
                self._capability[ATTR_SWITCH] = capa
                self._capability[capa.get(CONF_CAPABILITY)] = capa
            elif ATTR_MODE in capa:
                self._capability[ATTR_MODE] = capa
            elif ATTR_FAN_MODE in capa:
                self._capability[ATTR_FAN_MODE] = capa
                self._supported_features |= ClimateEntityFeature.FAN_MODE
            elif ATTR_TARGET_TEMP in capa:
                self._capability[ATTR_TARGET_TEMP] = capa
                self._supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            elif ATTR_TARGET_TEMP_LOW in capa:
                self._capability[ATTR_TARGET_TEMP_LOW] = capa
            elif ATTR_TARGET_TEMP_HIGH in capa:
                self._capability[ATTR_TARGET_TEMP_HIGH] = capa
            elif ATTR_TARGET_HUM in capa:
                self._capability[ATTR_TARGET_HUM] = capa
                self._supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
            elif ATTR_CURRENT_TEMPERATURE in capa:
                self._capability[ATTR_CURRENT_TEMPERATURE] = capa
            elif ATTR_CURRENT_HUMIDITY in capa:
                self._capability[ATTR_CURRENT_HUMIDITY] = capa
            elif ATTR_PRESET_MODE in capa:
                self._capability[ATTR_PRESET_MODE] = capa
                self._supported_features |= ClimateEntityFeature.PRESET_MODE
            elif ATTR_SWING_MODE in capa:
                self._capability[ATTR_SWING_MODE] = capa
                self._supported_features |= ClimateEntityFeature.SWING_MODE
            elif ATTR_AUX_HEAT in capa:
                self._capability[ATTR_AUX_HEAT] = capa
                self._supported_features |= ClimateEntityFeature.AUX_HEAT

        if self._capability.get(ATTR_TARGET_TEMP_HIGH) and self._capability.get(ATTR_TARGET_TEMP_LOW):
            self._supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

        # external_entity
        if entity_id := self.get_attr_value(ATTR_SWITCH, CONF_ENTITY_ID):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, entity_id, self.entity_listener))

        if entity_id := self.get_attr_value(ATTR_CURRENT_TEMPERATURE, CONF_ENTITY_ID):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, entity_id, self.entity_listener))

        if entity_id := self.get_attr_value(ATTR_CURRENT_HUMIDITY, CONF_ENTITY_ID):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, entity_id, self.entity_listener))

        # modes
        if self.get_attr_value(ATTR_MODE, CONF_OPTIONS):
            mode = self.get_attr_value(ATTR_MODE, CONF_OPTIONS)
            # convert hvac_modes
            modes = ["off"]
            modes.extend(self.get_attr_value(ATTR_MODE, CONF_OPTIONS))
            modes = list(set(modes))
            hvac_modes = self.get_attr_value(ATTR_MODE, "s2h_mode_mapping", [{}])
            for mode in modes:
                self._hvac_modes.append(hvac_modes[0].get(mode, mode))

        
        # fan_modes
        if self.get_attr_value(ATTR_FAN_MODE, CONF_OPTIONS):
            mode = self.get_attr_value(ATTR_FAN_MODE, CONF_OPTIONS)
            # convert hvac_modes
            modes = []
            modes.extend(self.get_attr_value(ATTR_FAN_MODE, CONF_OPTIONS))
            modes = list(set(modes))
            fan_modes = self.get_attr_value(ATTR_FAN_MODE, "s2h_fan_mode_mapping", [{}])
            for mode in modes:
                self._fan_modes.append(fan_modes[0].get(mode, mode))

        
    def entity_listener(self, entity, old_state, new_state):
        self.schedule_update_ha_state(True)

    # platform property #############################################################################
    @property
    def is_on(self) -> bool:
        if entity_id := self.get_attr_value(ATTR_SWITCH, CONF_ENTITY_ID):
            return self.hass.states.get(entity_id).state != STATE_OFF
        return self.get_attr_value(ATTR_SWITCH, CONF_STATE) != STATE_OFF

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
        mode = self.get_attr_value(ATTR_MODE, CONF_STATE)
        hvac_modes = self.get_attr_value(ATTR_MODE, "s2h_mode_mapping", [{}])
        return hvac_modes[0].get(mode, mode)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return self._hvac_modes

    @property
    def fan_mode(self) -> str | None:
        mode = self.get_attr_value(ATTR_FAN_MODE, CONF_STATE)
        fan_modes = self.get_attr_value(ATTR_FAN_MODE, "s2h_fan_mode_mapping", [{}])
        return fan_modes[0].get(mode, mode)
    
    @property
    def fan_modes(self) -> list[str] | None:
        return self._fan_modes

    @property
    def target_temperature(self) -> float | None:
        return self.get_attr_value(ATTR_TARGET_TEMP, CONF_STATE)

    @property
    def target_temperature_high(self) -> float | None:
        return self.get_attr_value(ATTR_TARGET_TEMP_HIGH, CONF_STATE)

    @property
    def target_temperature_low(self) -> float | None:
        return self.get_attr_value(ATTR_TARGET_TEMP_LOW, CONF_STATE)


    @property
    def target_temperature_step(self) -> float | None:
        return self.get_attr_value(ATTR_TARGET_TEMP, "step")

    @property
    def current_temperature(self) -> float | None:
        # external temperature entity
        if entity_id := self.get_attr_value(ATTR_CURRENT_TEMPERATURE, CONF_ENTITY_ID):
            state = self.hass.states.get(entity_id)
            return state.state if is_valid_state(state) else None
        else:
            _LOGGER.debug("current_temperature : " +
                          str(ATTR_CURRENT_TEMPERATURE) + ", attr : " + str(CONF_STATE))
            return self.get_attr_value(ATTR_CURRENT_TEMPERATURE, CONF_STATE, 0)
            
    @property
    def max_temp(self) -> float:
        return self.get_attr_value(ATTR_TARGET_TEMP, "max", DEFAULT_MAX_TEMP)

    @property
    def min_temp(self) -> float:
        return self.get_attr_value(ATTR_TARGET_TEMP, "min", DEFAULT_MIN_TEMP)

    @property
    def current_humidity(self) -> int | None:
        # external humidity entity
        if entity_id := self.get_attr_value(ATTR_CURRENT_HUMIDITY, CONF_ENTITY_ID):
            state = self.hass.states.get(entity_id)
            return int(float(state.state)) if is_valid_state(state) else None
        else:
            hum = self.get_attr_value(ATTR_CURRENT_HUMIDITY, CONF_STATE, None)
            return int(float(hum)) if hum != None else None

    @property
    def target_humidity(self) -> int | None:
        return int(float(self.get_attr_value(ATTR_TARGET_HUM, CONF_STATE, None)))

    @property
    def max_humidity(self) -> int:
        return int(float(self.get_attr_value(ATTR_TARGET_HUM, "max", None)))

    @property
    def min_humidity(self) -> int:
        return int(float(self.get_attr_value(ATTR_TARGET_HUM, "min", DEFAULT_MIN_HUMIDITY)))
    
    @property
    def preset_mode(self) -> str | None:
        return self.get_attr_value(ATTR_PRESET_MODE, CONF_STATE)

    @property
    def preset_modes(self) -> list[str] | None:
        return self.get_attr_value(ATTR_PRESET_MODE, CONF_OPTIONS)

    @property
    def swing_mode(self) -> str | None:
        return self.get_attr_value(ATTR_SWING_MODE, CONF_STATE)

    @property
    def swing_modes(self) -> list[str] | None:
        return self.get_attr_value(ATTR_SWING_MODE, CONF_OPTIONS)

    @property
    def hvac_action(self) -> HVACAction | None:
        mode = self.get_attr_value(ATTR_MODE, CONF_STATE)
        if not self.is_on:
            mode = STATE_OFF
        actions = self.get_attr_value(ATTR_MODE, "s2h_action_mapping", [{}])
        return actions[0].get(mode, None)
        
    @property
    def is_aux_heat(self) -> bool | None:
        mode = self.get_attr_value(ATTR_AUX_HEAT, CONF_STATE)
        aux_heat_modes = self.get_attr_value(ATTR_AUX_HEAT, "aux_heat_modes", {})
        return mode in (aux_heat_modes)
    

    # # method ########################################################################################
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if self._capability.get(ATTR_SWITCH) and hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        hvac_modes = self.get_attr_value(ATTR_MODE, "s2h_mode_mapping", [{}])
        mode = hvac_mode
        for k, v in hvac_modes[0].items():
            if v == hvac_mode:
                mode = k
                break
        if self._capability.get(ATTR_SWITCH) and not self.is_on:
            await self.async_turn_on()

        if mode != self.get_attr_value(ATTR_MODE, CONF_STATE):
            await self.send_command(ATTR_MODE, self.get_command(ATTR_MODE), [mode])
    
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.send_command(ATTR_PRESET_MODE, self.get_command(ATTR_PRESET_MODE), [preset_mode])

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        fan_modes = self.get_attr_value(ATTR_FAN_MODE, "s2h_fan_mode_mapping", [{}])
        mode = fan_mode
        for k, v in fan_modes[0].items():
            if v == fan_mode:
                mode = k
                break
        if mode != self.get_attr_value(ATTR_FAN_MODE, CONF_STATE):
            await self.send_command(ATTR_FAN_MODE, self.get_command(ATTR_FAN_MODE), [mode])

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self.send_command(ATTR_SWING_MODE, self.get_command(ATTR_SWING_MODE), [swing_mode])
        
    async def async_set_humidity(self, humidity: int) -> None:
        await self.send_command(ATTR_TARGET_HUM, self.get_command(ATTR_TARGET_HUM), [humidity])

    async def async_set_temperature(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if key != "entity_id":
                if key == "temperature": key = ATTR_TARGET_TEMP
                await self.send_command(key, self.get_command(key), [value])

    async def async_turn_on(self) -> None:
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH).get(STATE_ON), self.get_argument(ATTR_SWITCH).get(STATE_ON, []))
        
    async def async_turn_off(self) -> None:
        _LOGGER.error("call async_turn_off")
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH).get(STATE_OFF), self.get_argument(ATTR_SWITCH).get(STATE_OFF, []))
    
    async def async_turn_aux_heat_off(self) -> None:
        await self.send_command(ATTR_AUX_HEAT, self.get_command(ATTR_AUX_HEAT).get(STATE_OFF), self.get_argument(ATTR_AUX_HEAT).get(STATE_OFF, []))
        
    async def async_turn_aux_heat_on(self) -> None:
        await self.send_command(ATTR_AUX_HEAT, self.get_command(ATTR_AUX_HEAT).get(STATE_ON), self.get_argument(ATTR_AUX_HEAT).get(STATE_ON, []))
