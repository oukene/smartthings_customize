import os
import yaml
from homeassistant.const import Platform
from .const import DOMAIN, CUSTOM_PLATFORMS, GLOBAL_SETTING, DEVICE_SETTING, PLATFORMS, CONF_CAPABILITY, CONF_ATTRIBUTE
import logging
_LOGGER = logging.getLogger(__name__)

def get_attribute(device, component, capability, attribute):
    try:
        return device.status._status.get(component).get(capability).get(attribute)
    except:
        return None

def get_attribute_value(device, component, capability, attribute):
    try:
        return device.status._status.get(component).get(capability).get(attribute).value
    except:
        return None

def get_attribute_unit(device, component, capability, attribute):
    try:
        return device.status._status.get(component).get(capability).get(attribute).unit
    except:
        return None

def get_attribute_data(device, component, capability, attribute):
    try:
        return device.status._status.get(component).get(capability).get(attribute).data
    except:
        return None

    # if component == "main":
    #     return device.status.attributes.get(attribute)
    # else:
    #     return device.status._components.get(component).attributes.get(attribute) if device.status._components.get(component) != None else None

class ExtraCapability():
    def __init__(self) -> None:
        self._extra_capability = {}

    def is_enable_feature(self, capa):
        return capa in self._extra_capability

    def get_extra_capa_attr_value(self, key, attr):
        try:
            value = self._extra_capability[key].get(attr)
            if str(type(value)) == "<class 'dict'>":
                capa = value.get(CONF_CAPABILITY) if value.get(CONF_CAPABILITY) != None else self._extra_capability[key][key]
                value = get_attribute_value(self._device, self._component, capa, value.get(CONF_ATTRIBUTE))
            return value
        except:
            return None

    def get_extra_capa_command(self, key):
        try:
            return self._extra_capability[key].get("commands").get("command")
        except:
            _LOGGER.debug("not found extra capa command : " + key)
            return None
        
    def get_extra_capa_capability(self, key):
        try:
            return self._extra_capability[key][key]
        except:
            _LOGGER.debug("not found extra capa : " + key)
            return None

    def get_extra_capa(self, key):
        try:
            return self._extra_capability[key]
        except:
            _LOGGER.debug("not found extra capa : " + key)
            return None


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
            self._platforms = set()
            self._default_settings = None
            #self.load_setting()

            cls._init = True

    def load_setting(self):
        # 셋팅을 로드
        filepath = DOMAIN + "/" + self._location.name + ".yaml"
        if os.path.isdir(DOMAIN) == False:
            os.makedirs(DOMAIN)
        if os.path.isfile(filepath) == False:
            with open(filepath, "w") as f:
                f.write("enable_default_entities : true\n\n")
                f.write("globals:\n\n")
                f.write("devices:\n\n")
                f.write("ignore_platforms: []\n\n")
                f.write("enable_syntax_property: true\n\n")
                f.write("default_entity_id_format: '"'st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}'"'\n\n")
                pass
        
        with open(filepath) as f:
            self._settings = yaml.load(f, Loader=yaml.FullLoader)
            _LOGGER.debug("full settings error : " + str(self._settings))

        self.build_platform()

    @staticmethod
    def get_default_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(GLOBAL_SETTING)
        except Exception as e:
            _LOGGER.debug("get_default_setting error : " + str(e))
            return None

    @staticmethod
    def get_device_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(DEVICE_SETTING)
        except Exception as e:
            _LOGGER.debug("get_device_setting error : " + str(e))
            return None

    @staticmethod
    def get_capabilities():
        setting = SettingManager()
        capabilities = []
        try:
            mgr = SettingManager()
            setting = mgr._settings.get(GLOBAL_SETTING)
            if setting != None:
                for platform in CUSTOM_PLATFORMS.values():
                    #_LOGGER.error("get_capa capabilities0 : " + str(setting.get(platform)))
                    if setting.get(platform):
                        for cap in setting.get(platform):
                            capabilities.append(cap.get("capability"))
                #_LOGGER.error("get_capa capabilities1 : " + str(capabilities))
            settings = mgr._settings.get(DEVICE_SETTING)
            if settings != None:
                for setting in settings:
                    for platform in CUSTOM_PLATFORMS.values():
                        if setting.get(platform):
                            for cap in setting[platform]:
                                capabilities.append(cap.get("capability"))
        except Exception as e:
            _LOGGER.debug("get_capabilities error : " + str(e))
            pass
        finally:
            return capabilities

    @staticmethod
    def get_capa_settings(broker, custom_platform):
        element_type = "commands"
        if custom_platform in (CUSTOM_PLATFORMS[Platform.SENSOR], CUSTOM_PLATFORMS[Platform.BINARY_SENSOR], CUSTOM_PLATFORMS[Platform.CLIMATE], CUSTOM_PLATFORMS[Platform.FAN]):
            element_type = "attributes"
        settings = []
        try:
            default_setting = SettingManager.get_default_setting().get(custom_platform)
            if default_setting != None:
                for cap in default_setting:
                    for device in broker.devices.values():
                        if SettingManager.is_allow_device_custom(device.device_id):
                            capabilities = broker.build_capability(device)
                            for key, value in capabilities.items():
                                if cap.get("component") == key and cap.get("capability") in value:
                                    for setting in cap.get(element_type):
                                        _LOGGER.debug("add setting : " + str(setting))
                                        settings.append([device, cap, setting])
        except Exception as e:
            _LOGGER.debug("get_capa_settings_1 error : " + str(e))
            pass
        
        try:
            for device_setting in SettingManager.get_device_setting():
                if device_setting["device_id"] in broker.devices:
                    capabilities = broker.build_capability(broker.devices[device_setting["device_id"]])
                    if custom_platform not in device_setting: 
                        continue
                    for cap in device_setting[custom_platform]:
                        if cap.get("component") in capabilities and cap.get("capability") in capabilities[cap.get("component")]:
                            for setting in cap.get(element_type):
                                _LOGGER.debug("add setting : " + str(setting))
                                settings.append([broker.devices[device_setting["device_id"]], cap, setting])
        except Exception as e:
            _LOGGER.debug("get_capa_settings_2 error : " + str(e))
            pass

        return settings

    @staticmethod
    def default_entity_id_format() -> str:
        try:
            return SettingManager()._settings.get("default_entity_id_format")
        except Exception as e:
            _LOGGER.debug("default_entity_id_format error : " + str(e))
            return False 

    @staticmethod
    def enable_syntax_property() -> bool:
        try:
            return SettingManager()._settings.get("enable_syntax_property")
        except Exception as e:
            _LOGGER.debug("enable_syntax_property error : " + str(e))
            return False


    @staticmethod
    def enable_default_entities() -> bool:
        try:
            mgr = SettingManager()
            return mgr._settings.get("enable_default_entities")
        except Exception as e:
            _LOGGER.debug("enable_default_entities : " + str(e))
            return False

    @staticmethod
    def is_allow_device(device_id) -> bool:
        try:
            mgr = SettingManager()
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
        except Exception as e:
            _LOGGER.debug("is_allow_device error : " + str(e))
            return True

    @staticmethod
    def is_allow_device_custom(device_id) -> bool:
        try:
            mgr = SettingManager()
            setting = mgr.get_device_setting()
            if setting != None:
                for d in mgr.get_device_setting():
                    if device_id == d.get("device_id"): return False
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
        except Exception as e:
            _LOGGER.debug("is_allow_device_custom error : " + str(e))
            return True

    def build_platform(self):
        self._platforms.clear()
        for platform in PLATFORMS:
            if self.is_allow_platform(platform):
                self._platforms.add(platform)

    def get_enable_platforms(self) -> set:
        return self._platforms

    def is_allow_platform(self, platform) -> bool:
        try:
            mgr = SettingManager()
            return platform not in mgr._settings.get("ignore_platforms")
        except Exception as e:
            _LOGGER.debug("is_allow_platform error : " + str(e))
            return True 

    @staticmethod
    def ignore_platforms():
        try:
            mgr = SettingManager()
            return mgr._settings.get("ignore_platforms")
        except Exception as e:
            _LOGGER.debug("ignore_platforms error : " + str(e))
            return []

    @staticmethod
    def ignore_capabilities():
        try:
            mgr = SettingManager()
            return mgr._settings.get(GLOBAL_SETTING).get("ignore_capabilities")
        except Exception as e:
            _LOGGER.debug("is_allow_device error : " + str(e))
            return None