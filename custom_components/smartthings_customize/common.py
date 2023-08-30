import os
import yaml
from .const import DOMAIN, CUSTOM_PLATFORMS, GLOBAL_SETTING, DEVICE_SETTING, CAPABILITY
import logging
_LOGGER = logging.getLogger(__name__)


def get_attribute(device, component, attribute):
    if component == "main":
        return device.status.attributes.get(attribute)
    else:
        return device.status._components.get(component).attributes.get(attribute) if device.status._components.get(component) != None else None


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
                pass
        
        with open(filepath) as f:
            self._settings = yaml.load(f, Loader=yaml.FullLoader)
            _LOGGER.error("full settings : " + str(self._settings))

        # filepath = DOMAIN + "/" + "default" + ".yaml"
        # if os.path.isfile(filepath) == False:
        #     with open(filepath, "w") as f:
        #         pass

        # with open(filepath) as f:
        #     self._default_settings = yaml.load(f, Loader=yaml.FullLoader)
        #     _LOGGER.error("full settings : " + str(self._default_settings))

    @staticmethod
    def get_default_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(GLOBAL_SETTING)
        except:
            return None

    @staticmethod
    def get_device_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(DEVICE_SETTING)
        except:
            return None

    @staticmethod
    def get_capabilities():
        setting = SettingManager()
        capabilities = []
        try:
            mgr = SettingManager()
            # for platform in CUSTOM_PLATFORMS:
            #     _LOGGER.error("get_capa capabilities0 : " + str(mgr._default_settings.get(platform)))
            #     if mgr._default_settings.get(platform):
            #         for cap in mgr._default_settings.get(platform):
            #             capabilities.append(cap.get("capability"))
            # _LOGGER.error("get_capa capabilities1 : " + str(capabilities))
            
            setting = mgr._settings.get(GLOBAL_SETTING)
            if setting != None:
                for platform in CUSTOM_PLATFORMS:
                    #_LOGGER.error("get_capa capabilities0 : " + str(setting.get(platform)))
                    if setting.get(platform):
                        for cap in setting.get(platform):
                            capabilities.append(cap.get("capability"))
                #_LOGGER.error("get_capa capabilities1 : " + str(capabilities))
            settings = mgr._settings.get(DEVICE_SETTING)
            _LOGGER.error("capa1 setting : " + str(settings))
            if settings != None:
                for setting in settings:
                    _LOGGER.error("capa2 setting : " + str(setting))
                    for platform in CUSTOM_PLATFORMS:
                        if setting.get(platform):
                            for cap in setting[platform]:
                                capabilities.append(cap.get("capability"))
                _LOGGER.error("get_capa capabilities2 : " + str(capabilities))
        except Exception as error:
            #capabilities.clear()
            pass
        finally:
            return capabilities

    @staticmethod
    def get_capa_settings(broker, custom_platform):
        capa_type = "commands"
        if custom_platform in ('sensors', 'binary_sensors'):
            capa_type = "attributes"
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
                                    for setting in cap.get(capa_type):
                                        _LOGGER.debug("add setting : " + str(setting))
                                        settings.append([device, cap, setting])
        except:
            pass
        
        try:
            for device_setting in SettingManager.get_device_setting():
                if device_setting["device_id"] in broker.devices:
                    capabilities = broker.build_capability(broker.devices[device_setting["device_id"]])
                    if custom_platform not in device_setting: 
                        continue
                    for cap in device_setting[custom_platform]:
                        if cap.get("component") in capabilities and cap.get("capability") in capabilities[cap.get("component")]:
                            for setting in cap.get(capa_type):
                                _LOGGER.debug("add setting : " + str(setting))
                                settings.append([broker.devices[device_setting["device_id"]], cap, setting])
        except Exception as e:
            #_LOGGER.error("get_capa_settings error" + str(e))
            pass

        return settings


    @staticmethod
    def enable_default_entities() -> bool:
        try:
            mgr = SettingManager()
            return mgr._settings.get("enable_default_entities")
        except:
            return False

    @staticmethod
    def is_allow_device(device_id) -> bool:
        try:
            mgr = SettingManager()
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
        except Exception as e:
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
            return True

    @staticmethod
    def is_allow_platform(platform) -> bool:
        try:
            mgr = SettingManager()
            return platform not in mgr._settings.get("ignore_platforms")
        except:
            return False

    @staticmethod
    def ignore_platforms():
        try:
            mgr = SettingManager()
            return mgr._settings.get("ignore_platforms")
        except:
            return []