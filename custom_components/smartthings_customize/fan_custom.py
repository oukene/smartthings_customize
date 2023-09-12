from . import SmartThingsEntity
from homeassistant.components.fan import *

from homeassistant.helpers.event import async_track_state_change

from .const import *
from .common import *

from homeassistant.const import *
import logging
_LOGGER = logging.getLogger(__name__)

ATTR_SWITCH = "switch"

class SmartThingsFan_custom(SmartThingsEntity_custom, FanEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("climate settings : " + str(setting[1]))

        self._supported_features = 0
        self._extra_capability = {}
        
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
            
        # external_entity
        if entity_id := self.get_attr_value(ATTR_SWITCH, CONF_ENTITY_ID):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, entity_id, self.entity_listener))

    def entity_listener(self, entity, old_state, new_state):
        self.schedule_update_ha_state(True)
    
    # platform property #############################################################################
    @property
    def is_on(self) -> bool | None:
        if entity_id := self.get_attr_value(ATTR_SWITCH, CONF_ENTITY_ID):
            return self.hass.states.get(entity_id).state != STATE_OFF
        return self.get_attr_value(ATTR_SWITCH, CONF_STATE) != STATE_OFF

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
        return self.get_attr_value(ATTR_PERCENTAGE, CONF_STATE)

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
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH).get(STATE_ON), self.get_argument(ATTR_SWITCH).get(STATE_ON, []))
        if percentage:
            await self.async_set_percentage(percentage)
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.send_command(ATTR_SWITCH, self.get_command(ATTR_SWITCH).get(STATE_OFF), self.get_argument(ATTR_SWITCH).get(STATE_OFF, []))

    async def async_set_direction(self, direction: str) -> None:
        await self.send_command(ATTR_DIRECTION, self.get_command(ATTR_DIRECTION), [direction])

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.send_command(ATTR_PRESET_MODE, self.get_command(ATTR_PRESET_MODE), [preset_mode])
        
    async def async_set_percentage(self, percentage: int) -> None:
        await self.send_command(ATTR_PERCENTAGE, self.get_command(ATTR_PERCENTAGE), [percentage])

    async def async_oscillate(self, oscillating: bool) -> None:
        try:
            if mode := self.get_attr_value(ATTR_DIRECTION, "oscillate_mode")[0]:
                await self.send_command(ATTR_DIRECTION, self.get_command(ATTR_DIRECTION), [mode])
        except:
            pass
