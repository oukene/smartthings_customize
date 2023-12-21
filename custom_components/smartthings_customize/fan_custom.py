from homeassistant.const import MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION
from homeassistant.util.percentage import ordered_list_item_to_percentage, percentage_to_ordered_list_item, ranged_value_to_percentage, percentage_to_ranged_value

try:
    from homeassistant.util.scaling import int_states_in_range
except ImportError:
    from homeassistant.util.percentage import int_states_in_range

from homeassistant.components.fan import *
from .const import *
from .common import *

from homeassistant.const import *
import logging
_LOGGER = logging.getLogger(__name__)

ATTR_SWITCH = "switch"

class SmartThingsFan_custom(SmartThingsEntity_custom, FanEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("fan settings : " + str(setting[1]))
        self._supported_features = 0
        
        for capa in setting[1]["capabilities"]:
            if ATTR_SWITCH in capa:
                self._capability[ATTR_SWITCH] = capa
            elif ATTR_PRESET_MODE in capa:
                self._capability[ATTR_PRESET_MODE] = capa
                self._supported_features |= FanEntityFeature.PRESET_MODE
            elif ATTR_DIRECTION in capa:
                self._capability[ATTR_DIRECTION] = capa
                self._supported_features |= FanEntityFeature.DIRECTION
                if self.get_attr_value(ATTR_DIRECTION, "oscillate_modes"):
                    self._supported_features |= FanEntityFeature.OSCILLATE
            elif ATTR_PERCENTAGE in capa:
                self._capability[ATTR_PERCENTAGE] = capa
                self._supported_features |= FanEntityFeature.SET_SPEED
        
        self._speed_list = self.get_attr_value(ATTR_PERCENTAGE, CONF_SPEED_LIST, None)
        self._speed_range = (float(self.get_attr_value(ATTR_PERCENTAGE, "min", 1)), float(self.get_attr_value(ATTR_PERCENTAGE, "max", 100)))

        # external_entity
        # if entity_id := self.get_attr_value(ATTR_SWITCH, CONF_ENTITY_ID):
        #     self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
        #         self._hass, entity_id, self.entity_listener))

    def entity_listener(self, entity, old_state, new_state):
        self.schedule_update_ha_state(True)
    
    # platform property #############################################################################
    @property
    def is_on(self) -> bool | None:
        value = self.get_attr_value(Platform.SWITCH, CONF_STATE, STATE_OFF)
        on_state = self.get_attr_value(Platform.SWITCH, ON_STATE, [STATE_ON])
        return value in on_state

    @property
    def current_direction(self) -> str | None:
        return self.get_attr_value(ATTR_DIRECTION, CONF_STATE)
    
    @property
    def oscillating(self) -> bool | None:
        mode = self.get_attr_value(ATTR_DIRECTION, CONF_STATE)
        oscillate_modes = self.get_attr_value(ATTR_DIRECTION, "oscillate_modes", [])
        return mode in oscillate_modes

    @property
    def percentage(self) -> int | None:
        current_speed = self.get_attr_value(ATTR_PERCENTAGE, CONF_STATE, 0)
        if self._speed_list is not None:
            return ordered_list_item_to_percentage(self._speed_list, current_speed)

        if current_speed > self._speed_range[1]:
            current_speed = self._speed_range[1]
        return ranged_value_to_percentage(self._speed_range, float(current_speed))

    @property
    def speed_count(self) -> int:
        if self._speed_list is not None:
            return len(self._speed_list)
            
        return int_states_in_range(self._speed_range)

    @property
    def percentage_step(self) -> float:
        return self.get_attr_value(ATTR_PERCENTAGE, "step", 1)

    @property
    def preset_mode(self) -> str | None:
        return self.get_attr_value(ATTR_PRESET_MODE, CONF_STATE)

    @property
    def preset_modes(self) -> list[str] | None:
        return self.get_attr_value(ATTR_PRESET_MODE, CONF_OPTIONS)

    @property
    def supported_features(self) -> int | None:
        return self._supported_features
    
    # method ########################################################################################
    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH, {STATE_ON:STATE_ON}).get(STATE_ON), self.get_argument(ATTR_SWITCH, {STATE_ON:[]}).get(STATE_ON, []))
        if percentage:
            value = int(math.ceil(percentage_to_ranged_value(self._speed_range, percentage)))
            await self.send_command(ATTR_PERCENTAGE, self.get_command(ATTR_PERCENTAGE), [value])
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH, {STATE_OFF: STATE_OFF}).get(STATE_OFF), self.get_argument(ATTR_SWITCH, {STATE_OFF:[]}).get(STATE_OFF, []))

    async def async_set_direction(self, direction: str) -> None:
        if not self.is_on:
            await self.async_turn_on()
        await self.send_command(ATTR_DIRECTION, self.get_command(ATTR_DIRECTION), [direction])

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if not self.is_on:
            await self.async_turn_on()
        await self.send_command(ATTR_PRESET_MODE, self.get_command(ATTR_PRESET_MODE), [preset_mode])
        
    async def async_set_percentage(self, percentage: int) -> None:
        if le(percentage, 0):
            await self.async_turn_off()
            return
            
        if not self.is_on:
            await self.async_turn_on()

        value = int(math.ceil(percentage_to_ranged_value(self._speed_range, percentage)))
        await self.send_command(ATTR_PERCENTAGE, self.get_command(ATTR_PERCENTAGE), [value])

    async def async_oscillate(self, oscillating: bool) -> None:
        try:
            if mode := self.get_attr_value(ATTR_DIRECTION, "oscillate_mode")[0]:
                await self.send_command(ATTR_DIRECTION, self.get_command(ATTR_DIRECTION), [mode])
        except:
            pass
