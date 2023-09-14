"""Support for texts through the SmartThings cloud API."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pysmartthings import Capability

from homeassistant.components.vacuum import *
from homeassistant.components.vacuum import VacuumEntity as v
from homeassistant.const import *
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .common import *

import logging
_LOGGER = logging.getLogger(__name__)

CONF_COMMANDS = "commands"
CONF_FAN_SPEED = "fan_speed"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]

    entities = []
    settings = SettingManager.get_capa_settings(broker, Platform.VACUUM)
    for s in settings:
        _LOGGER.debug("cap setting : " + str(s[1]))
        entities.append(SmartThingsVacuum_custom(hass=hass, setting=s))

    async_add_entities(entities)


class SmartThingsVacuum_custom(SmartThingsEntity_custom, StateVacuumEntity):
    def __init__(self, hass, setting) -> None:
        super().__init__(hass, platform=Platform.VACUUM, setting=setting)

        self._supported_features = 0
        self._fan_speed_list = []
        for capa in setting[1]["capabilities"]:
            if "commands" in capa:
                self._capability["commands"] = capa
                self._supported_features |= VacuumEntityFeature.RETURN_HOME
                #self._supported_features |= VacuumEntityFeature.CLEAN_SPOT
                self._supported_features |= VacuumEntityFeature.STOP
                self._supported_features |= VacuumEntityFeature.START
                #self._supported_features |= VacuumEntityFeature.LOCATE
                self._supported_features |= VacuumEntityFeature.STATE
                self._supported_features |= VacuumEntityFeature.SEND_COMMAND

            elif "fan_speed" in capa:
                self._capability["fan_speed"] = capa
                self._supported_features |= VacuumEntityFeature.FAN_SPEED
            elif "battery" in capa:
                self._capability["battery"] = capa
                self._supported_features |= VacuumEntityFeature.BATTERY

        # fan_modes
        if self.get_attr_value("fan_speed", CONF_OPTIONS):
            mode = self.get_attr_value("fan_speed", CONF_OPTIONS)
            # convert hvac_modes
            modes = []
            modes.extend(self.get_attr_value("fan_speed", CONF_OPTIONS))
            modes = list(set(modes))
            fan_modes = self.get_attr_value(
                "fan_speed", "s2h_fan_speed_mapping", [{}])
            for mode in modes:
                self._fan_speed_list.append(fan_modes[0].get(mode, mode))

    @property
    def fan_speed_list(self) -> list[str]:
        return self._fan_speed_list

    @property
    def supported_features(self) -> int | None:
        return self._supported_features

    @property
    def state(self) -> str | None:
        """Return the state of the vacuum cleaner."""
        if state := self.get_attr_value("commands", CONF_STATE):
            if state == "cleaning":
                return STATE_CLEANING
            elif state in ("charging", "charged"):
                return STATE_DOCKED
            elif state == "idle":
                return STATE_IDLE
            elif state == "homing":
                return STATE_RETURNING
            else:
                return state
        else:
            return STATE_ERROR

    # @property
    # def battery_level(self) -> int | None:
    #     """Return the battery level of the vacuum cleaner."""
    #     return self.get_attr_status("battery", "battery")

    # @property
    # def battery_icon(self) -> str:
    #     """Return the battery icon for the vacuum cleaner."""
    #     return icon_for_battery_level(
    #         battery_level=self.get_attr_status("battery", "battery"), charging=(self.state == STATE_DOCKED)
    #     )

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        speed = self.get_attr_value("fan_speed", CONF_STATE)
        fan_speed = self.get_attr_value("fan_speed", "s2h_fan_speed_mapping", [{}])
        return fan_speed[0].get(speed, speed)

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self.send_command(CONF_COMMANDS, self.get_command(CONF_COMMANDS), self.get_argument(CONF_COMMANDS).get("return"))
        
    async def async_start(self, **kwargs: Any) -> None:
        """Turn the vacuum on and start cleaning."""
        await self.send_command(CONF_COMMANDS, self.get_command(CONF_COMMANDS), self.get_argument(CONF_COMMANDS).get("start"))

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the vacuum cleaner."""
        await self.send_command(CONF_COMMANDS, self.get_command(CONF_COMMANDS), self.get_argument(CONF_COMMANDS).get("stop"))

    # def clean_spot(self, **kwargs: Any) -> None:
    #     """Perform a spot clean-up."""
    #     _LOGGER.error("call clean spot, arg: " + str(kwargs))
    #     # self.device.run(sucks.Spot())

    # def locate(self, **kwargs: Any) -> None:
    #     """Locate the vacuum cleaner."""
    #     # self.device.run(sucks.PlaySound())

    async def set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        fan_modes = self.get_attr_value(CONF_FAN_SPEED, "s2h_fan_speed_mapping", [{}])
        mode = fan_speed
        for k, v in fan_modes[0].items():
            if v == fan_speed:
                mode = k
                break
        if mode != self.get_attr_value(CONF_FAN_SPEED, CONF_STATE):
            await self.send_command(CONF_FAN_SPEED, self.get_command(CONF_FAN_SPEED), [mode])


    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to a vacuum cleaner."""
        _LOGGER.error("send command!!!")
