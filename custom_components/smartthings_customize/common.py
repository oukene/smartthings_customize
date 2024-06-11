import os
import yaml
import traceback
from homeassistant.const import Platform, CONF_TYPE
from .const import *
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, CONF_ICON, CONF_VALUE_TEMPLATE,
)
import homeassistant.helpers.config_validation as cv
from pysmartthings.device import DeviceEntity
from .const import *

from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

from homeassistant.helpers.entity import DeviceInfo, Entity
import string
import logging
from time import time
from operator import *
_LOGGER = logging.getLogger(__name__)


def is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE and state.state != None

class format_util(string.Template):
    delimiter = "%"


class SmartThingsEntity_custom(Entity):
    """Defines a SmartThings entity."""

    _attr_should_poll = False

    def __init__(self, hass, platform: Platform, setting) -> None:
        """Initialize the instance."""
        self._hass = hass
        self._device = setting[0]

        component = setting[1].get(CONF_COMPONENT)
        capability = setting[1].get(CONF_CAPABILITY)
        name = setting[1].get(CONF_NAME)
        attribute = setting[1].get(CONF_ATTRIBUTE)
        command = setting[1].get(CONF_COMMAND)
        #argument = setting[1].get(CONF_ARGUMENT)
        parent_entity_id = setting[1].get(CONF_PARENT_ENTITY_ID)
        self._icon = setting[1].get(CONF_ICON)

        self._extra_state_attributes = {}
        if SettingManager.enable_syntax_property():
            self._extra_state_attributes[ATTR_SYNTAX] = setting[1]

        self._dispatcher_remove = None
        self._device_info = []
        self._platform = platform

        self._capability = {}
        self._capability[platform] = setting[1]

        t = format_util(DEFAULT_UNIQUE_ID_FORMAT)
        unique_id_format = t.substitute(device_id=self._device.device_id, device_type=self._device.type, label=self._device.label, component=component,
                                        capability=capability, attribute=attribute, command=command, name=name)
        self._unique_id = "{}".format(platform + "." + unique_id_format)

        entity_id_format = SettingManager.default_entity_id_format(
        ) if SettingManager.default_entity_id_format() != None else DEFAULT_ENTITY_ID_FORMAT
        if setting[1].get(CONF_ENTITY_ID_FORMAT) != None:
            entity_id_format = setting[1].get(CONF_ENTITY_ID_FORMAT)
        t = format_util(entity_id_format)
        entity_id_format = t.substitute(device_id=self._device.device_id, device_type=self._device.type, label=self._device.label, component=component,
                                        capability=capability, attribute=attribute, command=command, name=name)
        self.entity_id = "{}".format(platform + "." + entity_id_format)

        t = format_util(name)
        self._name = t.substitute(device_id=self._device.device_id, device_type=self._device.type, label=self._device.label, component=component,
                                  capability=capability, attribute=attribute, command=command, name=name)
        
        _LOGGER.debug("create entity id : %s", self.entity_id)

        registry = er.async_get(hass)

        source_entity = registry.async_get(parent_entity_id)
        dev_reg = dr.async_get(hass)
        # Resolve source entity device
        if (
            (source_entity is not None)
            and (source_entity.device_id is not None)
            and (
                (
                    device := dev_reg.async_get(
                        device_id=source_entity.device_id,
                    )
                )
                is not None
            )
        ):
            self._device_info = DeviceInfo(
                identifiers=device.identifiers,
                name=device.name,
                manufacturer=device.manufacturer,
                model=device.model,
                hw_version=device.hw_version,
                sw_version=device.sw_version,
            )
        else:
            self._device_info = DeviceInfo(
                identifiers={(DOMAIN, self._device.device_id)},
                name=self._device.label,
                manufacturer=self._device.status.ocf_manufacturer_name,
                model=self._device.status.ocf_model_number,
                hw_version=self._device.status.ocf_hardware_version,
                sw_version=self._device.status.ocf_firmware_version,
            )

    async def async_added_to_hass(self):
        """Device added to hass."""
        self.set_timestamp()
        async def async_update_state(devices, evt):
            """Update device state."""
            if self._device.device_id in devices:
                if eq(self._device.device_id, evt.device_id):
                    for key, cap in self._capability.items():
                        if eq(self.get_component(key), evt.component_id) and eq(self.get_capability(key), evt.capability):
                            self.set_timestamp()
                await self.async_update_ha_state(True)

        self._dispatcher_remove = async_dispatcher_connect(
            self.hass, SIGNAL_SMARTTHINGS_UPDATE, async_update_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect the device when removed."""
        if self._dispatcher_remove:
            self._dispatcher_remove()

    def set_timestamp(self):
        self._extra_state_attributes[CONF_LAST_TIMESTAMP] = time()

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    @property
    def device_info(self) -> DeviceInfo:
        """Get attributes about the device."""
        return DeviceInfo(
            configuration_url="https://account.smartthings.com",
            identifiers=self._device_info.get("identifiers"),
            connections=self._device_info.get("connections"),
            manufacturer=self._device.status.ocf_manufacturer_name,
            model=self._device.status.ocf_model_number,
            name=self._device_info.get("name"),
            hw_version=self._device.status.ocf_hardware_version,
            sw_version=self._device.status.ocf_firmware_version,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str | None:
        return self._unique_id

    @property
    def icon(self) -> str | None:
        return self._icon

    async def send_command(self, platform, command, arg):
        if arg_setting := self.get_argument(platform):
            if isinstance(arg_setting, dict):
                if arg_type := arg_setting.get(CONF_TYPE):
                    if isinstance(arg, list):
                        if arg_type == "float":
                            arg = list(map(float, arg))
                        elif arg_type == "str":
                            arg = list(map(str, arg))
                        elif arg_type == "int":
                            arg = list(map(int, arg))
                    else:
                        if arg_type == "float":
                            arg = float(arg)
                        elif arg_type == "str":
                            arg = str(arg)
                        elif arg_type == "int":
                            arg = int(arg)
            
        await self._device.command(self.get_component(platform), self.get_capability(platform), command, arg)
        self.async_write_ha_state()

    def is_enable_feature(self, capa):
        return capa in self._capability

    def get_component(self, platform):
        return self._capability[platform].get(CONF_COMPONENT, self._capability[self._platform].get(CONF_COMPONENT))

    def get_capability(self, platform):
        return self._capability[platform].get(CONF_CAPABILITY, self._capability[self._platform].get(CONF_CAPABILITY))

    def _get_attr_status(self, component, capability, attribute, default=None):
        try:
            return self._device.status._status.get(component).get(capability).get(attribute)
        except:
            return default

    def _get_attr_status_value(self, component, capability, attribute, default=None):
        try:
            return self._device.status._status.get(component).get(capability).get(attribute).value
        except:
            return default

    def _get_attr_status_unit(self, component, capability, attribute, default=None):
        try:
            return self._device.status._status.get(component).get(capability).get(attribute).unit
        except:
            return default

    # def _get_attribute_unit(self, component, capability, attribute):
    #     try:
    #         return self._device.status._status.get(component).get(capability).get(attribute).unit
    #     except:
    #         return None

    def get_attr_status(self, conf, platform, default = None):
        try:
            component = conf.get(CONF_COMPONENT, self.get_component(platform))
            capa = conf.get(CONF_CAPABILITY, self.get_capability(platform))
            _LOGGER.debug("get dict attr - platform : " + str(platform) + ", component : " + str(component) + ", capa : " + str(capa) + ", default : " + str(default))
            return self._get_attr_status(component, capa, conf.get(CONF_ATTRIBUTE), default=default)
        except:
            return default

    def get_attr_unit(self, platform, default=None):
        conf = self._capability[platform].get(CONF_STATE, default)
        if str(type(conf)) == "<class 'dict'>":
            if status := self.get_attr_status(conf, platform):
                return status.unit
        return default

    def get_attr_value(self, platform, attr, default = None):
        try:
            #_LOGGER.debug("extra capa : " + str(self._capability[platform]))
            value = self._capability[platform].get(attr, default)
            #_LOGGER.debug("platform : " + str(platform) + ", attr : " + str(attr) + ", value: " + str(value) + ", type : " + str(type(value)))
            if isinstance(value, dict):
                # if status := self.get_attr_status(value, platform, default):
                #     _LOGGER.error("set status value: " + str(status.value))
                #     value = status.value
                
                # value_template check
                if value_template := value.get(CONF_VALUE_TEMPLATE):
                    value = cv.template(value_template).async_render()
                else:
                    component = value.get(CONF_COMPONENT, self.get_component(platform))
                    capa = value.get(CONF_CAPABILITY, self.get_capability(platform))
                    #_LOGGER.debug("get dict attr - platform : " + str(platform) + ", component : " + str(component) + ", capa : " + str(capa) + ", default : " + str(default))
                    value = self._get_attr_status_value(component, capa, value.get(CONF_ATTRIBUTE), default=default)
            return value
        except Exception as e:
            _LOGGER.debug("error : " + traceback.format_exc())

    def get_attribute(self, platform, default=None):
        try:
            return self._capability[platform].get(CONF_ATTRIBUTE, default)
        except:
            _LOGGER.debug("not found attribute : " + traceback.format_exc())
            return default

    def get_command(self, platform, default=None):
        try:
            return self._capability[platform].get(CONF_COMMAND, default)
        except:
            _LOGGER.debug("not found command : " + traceback.format_exc())
            return default

    def get_argument(self, platform, default=None):
        try:
            return self._capability[platform].get(CONF_ARGUMENT, default)
        except:
            _LOGGER.debug("not found argument : " + traceback.format_exc())
            return default

    def get_capabilities(self, platform, default=None):
        try:
            return self._capability[platform]
        except:
            _LOGGER.debug("not found capabilities : " + traceback.format_exc())
            return default

    def get_mapping_value(self, attr, mapping_option, key):
        data = self.get_attr_value(attr, mapping_option, [{}])
        return data[0].get(key, key)

    def get_mapping_key(self, attr, mapping_option, value):
        data = self.get_attr_value(attr, mapping_option, [{}])
        key = value
        for k, v in data[0].items():
            if eq(v, value):
                key = k
                break;
        return key

class SettingManager(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls) 
        return cls._instance

    def __init__(self, location = None):
        cls = type(self)
        if not hasattr(cls, "_init"):
            self._location = location
            self._settings = None
            self._options = {}
            self._platforms = set()
            self._default_settings = None
            #self.load_setting()

            cls._init = True

    def init(self, hass, location):
        self.hass = hass
        self._location = location

    def load_setting(self):
        # 셋팅을 로드
        def _load_setting():
            filepath = DOMAIN + "/" + self._location.name + ".yaml"
            if os.path.isdir(DOMAIN) == False:
                os.makedirs(DOMAIN)
            if os.path.isfile(filepath) == False:
                with open(filepath, "w") as f:
                    f.write("globals:\n\n")
                    f.write("devices:\n\n")
                    f.write("ignore_platforms: []\n\n")
                    f.write("default_entity_id_format: '"'st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}'"'\n\n")
                    pass
            
            with open(filepath, "r") as fp:
                self._settings = yaml.load(fp, Loader=yaml.FullLoader)
                _LOGGER.debug("full settings error : " + str(self._settings))

        self.hass.add_job(_load_setting)

        self.build_platform()

    @staticmethod
    def set_options(options):
        mgr = SettingManager()
        mgr._options = options

    @staticmethod
    def get_default_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(GLOBAL_SETTING)
        except Exception as e:
            _LOGGER.debug("get_default_setting error : " + traceback.format_exc())
            return None

    @staticmethod
    def get_device_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(DEVICE_SETTING)
        except Exception as e:
            _LOGGER.debug("get_device_setting error : " + traceback.format_exc())
            return None

    @staticmethod
    def get_capabilities() -> list[str]:
        setting = SettingManager()
        capabilities = []
        try:
            if default_setting := SettingManager.get_default_setting():
                for platform in PLATFORMS:
                    if default_setting.get(platform):
                        for cap in default_setting.get(platform):
                            capabilities.append(cap.get("capability")) 
                            for sub_cap in cap.get("capabilities", []):
                                capabilities.append(sub_cap.get("capability"))
            for setting in SettingManager().get_device_setting():
                for platform in PLATFORMS:
                    if setting.get(platform):
                        for cap in setting[platform]:
                            capabilities.append(cap.get("capability"))
                            for sub_cap in cap.get("capabilities", []):
                                capabilities.append(sub_cap.get("capability"))

            #capabilities.extend(mgr.subscribe_capabilities())
            _LOGGER.debug("get_capabilities : " + str(capabilities))
        except Exception as e:
            _LOGGER.debug("get_capabilities error : " + traceback.format_exc())
            pass
        finally:
            return capabilities

    @staticmethod
    def get_capa_settings(broker, platform):
        settings = []
        try:
            if default_setting := SettingManager.get_default_setting():
                if default_setting.get(platform):
                    for setting in default_setting.get(platform):
                        for device in broker.devices.values():
                            if SettingManager.allow_device_custom(device.device_id):
                                capabilities = broker.build_capability(device)
                                for key, value in capabilities.items():
                                    if setting.get("component") == key and setting.get("capability") in value:
                                        settings.append([device, setting])
        except Exception as e:
            _LOGGER.debug("get_capa_settings_1 error : " + traceback.format_exc())
            pass
        
        try:
            if s := SettingManager.get_device_setting():
                for device_setting in s:
                    if device_setting["device_id"] in broker.devices:
                        capabilities = broker.build_capability(broker.devices[device_setting["device_id"]])
                        if device_type := device_setting.get("type", None):
                            if device_type.lower() != broker.devices[device_setting["device_id"]].type.lower():
                                continue
                        if platform not in device_setting:
                            continue
                        for setting in device_setting.get(platform, []):
                            if setting.get("component") in capabilities and setting.get("capability") in capabilities[setting.get("component")]:
                                if parent_entity_id := device_setting.get("parent_entity_id", None):
                                    setting[CONF_PARENT_ENTITY_ID] = parent_entity_id
                                settings.append(
                                    [broker.devices[device_setting["device_id"]], setting])
        except Exception as e:
            _LOGGER.debug("get_capa_settings_2 error : " + traceback.format_exc())
            pass

        return settings

    @staticmethod
    def default_entity_id_format() -> str:
        try:
            return SettingManager()._settings.get("default_entity_id_format")
        except Exception as e:
            _LOGGER.debug("default_entity_id_format error : " + traceback.format_exc())
            return False 

    @staticmethod
    def enable_syntax_property() -> bool:
        return SettingManager()._options.get(CONF_ENABLE_SYNTAX_PROPERTY, False)


    @staticmethod
    def enable_default_entities() -> bool:
        return False
        #return SettingManager()._options.get(CONF_ENABLE_DEFAULT_ENTITIES, False)

    @staticmethod
    def resetting_entities() -> bool:
        return SettingManager()._options.get(CONF_RESETTING_ENTITIES, False)

    @staticmethod
    def allow_device(device_id) -> bool:
        try:
            mgr = SettingManager()
            return device_id not in mgr._settings.get(GLOBAL_SETTING, {}).get("ignore_devices", [])
        except Exception as e:
            _LOGGER.debug("allow_device error : " + traceback.format_exc())
            return True

    @staticmethod
    def allow_device_custom(device_id) -> bool:
        try:
            mgr = SettingManager()
            setting = mgr.get_device_setting()
            if setting != None:
                for d in mgr.get_device_setting():
                    if device_id == d.get("device_id"): return False
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
        except Exception as e:
            _LOGGER.debug("allow_device_custom error : " + traceback.format_exc())
            return True

    def build_platform(self):
        self._platforms.clear()
        for platform in PLATFORMS:
            if self.allow_platform(platform):
                self._platforms.add(platform)

    def get_enable_platforms(self) -> set:
        return self._platforms

    def allow_platform(self, platform) -> bool:
        try:
            mgr = SettingManager()
            return platform not in mgr._settings.get("ignore_platforms")
        except Exception as e:
            _LOGGER.debug("is_allow_platform error : " + traceback.format_exc())
            return True 

    @staticmethod
    def ignore_platforms():
        try:
            mgr = SettingManager()
            return mgr._settings.get("ignore_platforms")
        except Exception as e:
            _LOGGER.debug("ignore_platforms error : " + traceback.format_exc())
            return []

    @staticmethod
    def ignore_capabilities():
        try:
            mgr = SettingManager()
            return mgr._settings.get(GLOBAL_SETTING).get("ignore_capabilities", [])
        except Exception as e:
            _LOGGER.debug("ignore_capabilities error : " + traceback.format_exc())
            return []

    @staticmethod
    def subscribe_capabilities():
        try:
            mgr = SettingManager()
            return mgr._settings.get("subscribe_capabilities", [])
        except Exception as e:
            _LOGGER.debug("allow_capabilities error : " + traceback.format_exc())
            return []

    @staticmethod
    def allow_capability(capability):
        return capability not in SettingManager().ignore_capabilities()

    @staticmethod
    def ignore_capability(capability):
        return capability in SettingManager().ignore_capabilities()


class SmartThingsEntity(Entity):
    """Defines a SmartThings entity."""

    _attr_should_poll = False

    def __init__(self, device: DeviceEntity) -> None:
        """Initialize the instance."""
        self._device = device
        self._dispatcher_remove = None

    async def async_added_to_hass(self):
        """Device added to hass."""

        async def async_update_state(devices):
            """Update device state."""
            if self._device.device_id in devices:
                await self.async_update_ha_state(True)

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
