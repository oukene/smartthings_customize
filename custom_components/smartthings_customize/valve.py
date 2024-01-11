"""Support for switches through the SmartThings cloud API."""
from __future__ import annotations
from .common import *

import math

from homeassistant.components.valve import *
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.const import STATE_CLOSED, STATE_OPEN, STATE_CLOSING
from homeassistant.util.percentage import ranged_value_to_percentage, percentage_to_ranged_value

from .const import *

import logging
_LOGGER = logging.getLogger(__name__)

ATTR_VALVE = "valve"
ATTR_STOP = "stop"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]
    entities = []

    settings = SettingManager.get_capa_settings(broker, Platform.VALVE)
    for s in settings:
    
        entities.append(SmartThingsValve_custom(hass=hass, setting=s))

    async_add_entities(entities)


class SmartThingsValve_custom(SmartThingsEntity_custom, ValveEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.CLIMATE, setting=setting)
        _LOGGER.debug("valve setting : " + str(setting[1]))
        self._prev_position = None
        self._attr_reports_position = False
        self._percent_range = (0, 100)
        self._attr_device_class = setting[1].get(CONF_DEVICE_CLASS)
        self._target_position = None

        for capa in setting[1]["capabilities"]:
            if ATTR_VALVE in capa:
                self._capability[ATTR_VALVE] = capa
                if capa.get(CONF_COMMAND, {}).get(STATE_OPEN):
                    self._attr_supported_features |= ValveEntityFeature.OPEN
                if capa.get(CONF_COMMAND, {}).get(STATE_CLOSED):
                    self._attr_supported_features |= ValveEntityFeature.CLOSE
            elif ATTR_POSITION in capa:
                self._capability[ATTR_POSITION] = capa
                self._attr_supported_features |= ValveEntityFeature.SET_POSITION
                self._attr_reports_position = True
                open = float(self.get_attr_value(ATTR_POSITION, STATE_OPEN, 100))
                close = float(self.get_attr_value(ATTR_POSITION, STATE_CLOSED, 0))
                close = (close + 1 if open > close else close - 1)
                self._percent_range = (close, open)
            elif ATTR_STOP in capa:
                self._capability[ATTR_STOP] = capa
                self._attr_supported_features |= ValveEntityFeature.STOP
                
    # @property
    # def is_opening(self) -> bool | None:
    #     self.get_attr_value(Platform.VALVE, ATTR_CURRENT_POSITION, 0)

    #     return super().is_opening

    @property
    def is_closed(self) -> bool | None:
        state = self.get_attr_value(Platform.VALVE, CONF_STATE)
        open_state = self.get_attr_value(Platform.VALVE, "open_state")
        self._attr_is_closed = state not in open_state
        return self._attr_is_closed

    # @property
    # def is_closing(self) -> bool | None:
    #     return super().is_closing

    @property
    def current_valve_position(self) -> int | None:
        self._attr_current_valve_position = self.get_attr_value(ATTR_POSITION, CONF_STATE, self.get_attr_value(ATTR_POSITION, STATE_CLOSED))

        open = self.get_attr_value(ATTR_POSITION, STATE_OPEN)
        close = self.get_attr_value(ATTR_POSITION, STATE_CLOSED)
        self._attr_is_closed = True

        if eq(self._attr_current_valve_position, close):
            self._attr_is_closed = False

        if self._target_position is not None and self._target_position == self._attr_current_valve_position:
            self._attr_is_closing = False
            self._attr_is_opening = False
            self._target_position = None
        elif self._target_position is not None and self._target_position != self._attr_current_valve_position and self._prev_position is not None:
            if open > close:
                if self._attr_current_valve_position < self._prev_position:
                    self._attr_is_closing = True
                    self._attr_is_opening = False
                else:
                    self._attr_is_closing = False
                    self._attr_is_opening = True
            else:
                if self._attr_current_valve_position < self._prev_position:
                    self._attr_is_closing = False
                    self._attr_is_opening = True
                else:
                    self._attr_is_closing = True
                    self._attr_is_opening = False

        self._prev_position = self._attr_current_valve_position
        state = ranged_value_to_percentage(self._percent_range, float(self._attr_current_valve_position))
        return state

    async def async_close_valve(self) -> None:
        await self.send_command(ATTR_VALVE, self.get_command(ATTR_VALVE, {STATE_CLOSED: STATE_CLOSED}).get(STATE_CLOSED), self.get_argument(ATTR_VALVE, {STATE_CLOSED: []}).get(STATE_CLOSED, []))

    async def async_open_valve(self) -> None:
        await self.send_command(ATTR_VALVE, self.get_command(ATTR_VALVE, {STATE_OPEN: STATE_OPEN}).get(STATE_OPEN), self.get_argument(ATTR_VALVE, {STATE_OPEN: []}).get(STATE_OPEN, []))

    async def async_set_valve_position(self, position: int) -> None:
        value = int(math.ceil(percentage_to_ranged_value(self._percent_range, position)))
        #_LOGGER.error("async_set_position : " + str(position))
        self._target_position = value
        await self.send_command(ATTR_POSITION, self.get_command(ATTR_POSITION), [value])

        if self._capability.get(ATTR_VALVE):
            if eq(value, self.get_attr_value(ATTR_POSITION, STATE_CLOSED, 0)):
                await self.async_close_valve()
            else:
                await self.async_open_valve()

    async def async_stop_valve(self) -> None:
        self._target_position = None
        await self.send_command(ATTR_STOP, self.get_command(ATTR_STOP), self.get_argument(ATTR_STOP))

