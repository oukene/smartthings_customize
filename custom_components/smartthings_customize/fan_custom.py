from . import SmartThingsEntity, SmartThingsEntity_custom
from homeassistant.components.fan import *

from homeassistant.helpers.event import async_track_state_change

from .const import *
from .common import *

from homeassistant.const import *
import logging
_LOGGER = logging.getLogger(__name__)

ATTR_SWITCH = "switch"

class SmartThingsFan_custom(SmartThingsEntity_custom, FanEntity, ExtraCapability):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("climate settings : " + str(setting[2]))

        self._supported_features = 0
        self._extra_capability = {}
        
        for capa in setting[2]["capabilities"]:
            if ATTR_SWITCH in capa:
                self._extra_capability[ATTR_SWITCH] = capa
            elif ATTR_PRESET_MODE in capa:
                self._extra_capability[ATTR_PRESET_MODE] = capa
                self._supported_features |= FanEntityFeature.PRESET_MODE
            elif ATTR_OSCILLATING in capa:
                self._extra_capability[ATTR_DIRECTION] = capa
                self._supported_features |= FanEntityFeature.OSCILLATE
                self._supported_features |= FanEntityFeature.DIRECTION
            elif ATTR_PERCENTAGE in capa:
                self._extra_capability[ATTR_PERCENTAGE] = capa
                self._supported_features |= FanEntityFeature.SET_SPEED
            
        # external_entity
        if self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id"):
            self._hass.data[DOMAIN]["listener"].append(async_track_state_change(
                self._hass, self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id"), self.entity_listener))

    def entity_listener(self, entity, old_state, new_state):
        self.schedule_update_ha_state(True)
    
    # platform property #############################################################################
    @property
    def is_on(self) -> bool | None:
        entity_id = self.get_extra_capa_attr_value(ATTR_SWITCH, "entity_id")
        if entity_id:
            if self.hass.states.get(entity_id).state == "off":
                return False
        if get_attribute_value(self._device, self._component, ATTR_SWITCH, ATTR_SWITCH) == "off":
            return False

    @property
    def current_direction(self) -> str | None:
        return self.get_extra_capa_attr_value(ATTR_DIRECTION, "commands")

    @property
    def oscillate(self, oscillating: bool) -> None:
        mode = self.get_extra_capa_attr_value(ATTR_DIRECTION, "commands")
        oscillate_modes = self.get_extra_capa_attr_value(ATTR_DIRECTION, "oscillate_modes")
        return mode in oscillate_modes

    @property
    def percentage(self) -> int | None:
        return self.get_extra_capa_attr_value(ATTR_PERCENTAGE, "commands")

    @property
    def percentage_step(self) -> float:
        return self.get_extra_capa_attr_value(ATTR_PERCENTAGE, "step")


    @property
    def preset_mode(self) -> str | None:
        return self.get_extra_capa_attr_value(ATTR_PRESET_MODE, "commands")

    @property
    def preset_modes(self) -> list[str] | None:
        return self.get_extra_capa_attr_value(ATTR_PRESET_MODE, "options")

    @property
    def supported_features(self) -> int | None:
        return self._supported_features

    
    # method ########################################################################################
    # async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_TURN_ON, {
    #                                     "entity_id": self._origin_entity}, False)

    # def turn_on(self, **kwargs) -> None:
    #     return self.hass.services.call(PLATFORM, SERVICE_TURN_ON, {
    #                                     "entity_id": self._origin_entity}, False)

    # async def async_turn_off(self, **kwargs: Any) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_TURN_OFF, {
    #                                     "entity_id": self._origin_entity}, False)

    # def turn_off(self, **kwargs) -> None:
    #     return self.hass.services.call(PLATFORM, SERVICE_TURN_OFF, {
    #                                     "entity_id": self._origin_entity}, False)

    # async def async_set_direction(self, direction: str) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_SET_DIRECTION, {
    #                                     "entity_id": self._origin_entity, ATTR_DIRECTION : direction }, False)

    # def set_direction(self, direction: str) -> None:
    #     return self.hass.services.call(PLATFORM, SERVICE_SET_DIRECTION, {
    #                                     "entity_id": self._origin_entity, ATTR_DIRECTION : direction }, False)
    
    # async def async_set_preset_mode(self, preset_mode: str) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_SET_PRESET_MODE, {
    #                                     "entity_id": self._origin_entity, ATTR_PRESET_MODE : preset_mode }, False)
        

    # def set_preset_mode(self, preset_mode: str) -> None:
    #     """Set the preset mode of the fan."""
    #     return self.hass.services.call(PLATFORM, SERVICE_SET_PRESET_MODE, {
    #                                     "entity_id": self._origin_entity, ATTR_PRESET_MODE : preset_mode }, False)

    # async def async_set_percentage(self, percentage: int) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_SET_PERCENTAGE, {
    #                                     "entity_id": self._origin_entity, ATTR_PERCENTAGE : percentage }, False)

    # def set_percentage(self, percentage: int) -> None:
    #     """Set the speed percentage of the fan."""
    #     return self.hass.services.call(PLATFORM, SERVICE_SET_PERCENTAGE, {
    #                                     "entity_id": self._origin_entity, ATTR_PERCENTAGE : percentage }, False)

    # async def async_oscillate(self, oscillating: bool) -> None:
    #     return await self.hass.services.async_call(PLATFORM, SERVICE_OSCILLATE, {
    #                                     "entity_id": self._origin_entity, ATTR_OSCILLATING : oscillating }, False)

    # def oscillate(self, oscillating: bool) -> None:
    #     """Oscillate the fan."""
    #     return self.hass.services.call(PLATFORM, SERVICE_OSCILLATE, {
    #                                     "entity_id": self._origin_entity, ATTR_OSCILLATING : oscillating }, False)