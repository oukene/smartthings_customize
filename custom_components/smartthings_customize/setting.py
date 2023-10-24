import os
import yaml
import traceback
from .const import *


from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

import logging
_LOGGER = logging.getLogger(__name__)

class SettingManager(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, location=None):
        cls = type(self)
        if not hasattr(cls, "_init"):
            #self._location = location
            self._filepath = DOMAIN + "/" + location.name + ".yaml"
            self._settings = None
            self._options = {}
            self._platforms = set()
            self._default_settings = None
            # self.load_setting()

            cls._init = True

    def load_setting(self):
        # 셋팅을 로드
        if os.path.isdir(DOMAIN) == False:
            os.makedirs(DOMAIN)
        if os.path.isfile(self._filepath) == False:
            with open(self._filepath, "w") as f:
                f.write("globals:\n\n")
                f.write("\tignore_capabilities: []\n\n")
                f.write("\tignore_devices: []\n\n")
                f.write("devices:\n\n")
                f.write("ignore_platforms: []\n\n")
                f.write(
                    "default_entity_id_format: '"'st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}'"'\n\n")
                pass

        with open(self._filepath) as f:
            self._settings = yaml.load(f, Loader=yaml.FullLoader)
            _LOGGER.debug("full settings error : " + str(self._settings))

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
            _LOGGER.debug("get_default_setting error : " +
                          traceback.format_exc())
            return None

    @staticmethod
    def get_device_setting():
        try:
            mgr = SettingManager()
            return mgr._settings.get(DEVICE_SETTING)
        except Exception as e:
            _LOGGER.debug("get_device_setting error : " +
                          traceback.format_exc())
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

            # capabilities.extend(mgr.subscribe_capabilities())
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
            _LOGGER.debug("get_capa_settings_1 error : " +
                          traceback.format_exc())
            pass

        try:
            if s := SettingManager.get_device_setting():
                for device_setting in s:
                    if device_setting["device_id"] in broker.devices:
                        capabilities = broker.build_capability(
                            broker.devices[device_setting["device_id"]])
                        if device_type := device_setting.get("type", None):
                            if device_type.lower() != broker.devices[device_setting["device_id"]].type.lower():
                                continue
                        if platform not in device_setting:
                            continue
                        for setting in device_setting.get(platform, []):
                            if setting.get("component") in capabilities and setting.get("capability") in capabilities[setting.get("component")]:
                                settings.append(
                                    [broker.devices[device_setting["device_id"]], setting])
        except Exception as e:
            _LOGGER.debug("get_capa_settings_2 error : " +
                          traceback.format_exc())
            pass

        return settings

    @staticmethod
    def default_entity_id_format() -> str:
        try:
            return SettingManager()._settings.get("default_entity_id_format")
        except Exception as e:
            _LOGGER.debug("default_entity_id_format error : " +
                          traceback.format_exc())
            return False

    @staticmethod
    def enable_syntax_property() -> bool:
        return SettingManager()._options.get(CONF_ENABLE_SYNTAX_PROPERTY, False)

    @staticmethod
    def enable_default_entities() -> bool:
        return SettingManager()._options.get(CONF_ENABLE_DEFAULT_ENTITIES, True)

    @staticmethod
    def resetting_entities() -> bool:
        return SettingManager()._options.get(CONF_RESETTING_ENTITIES, False)

    @staticmethod
    def allow_device(device_id) -> bool:
        try:
            mgr = SettingManager()
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
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
                    if device_id == d.get("device_id"):
                        return False
            return device_id not in mgr._settings.get(GLOBAL_SETTING).get("ignore_devices")
        except Exception as e:
            _LOGGER.debug("allow_device_custom error : " +
                          traceback.format_exc())
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
            _LOGGER.debug("is_allow_platform error : " +
                          traceback.format_exc())
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
            _LOGGER.debug("ignore_capabilities error : " +
                          traceback.format_exc())
            return []

    @staticmethod
    def subscribe_capabilities():
        try:
            mgr = SettingManager()
            return mgr._settings.get("subscribe_capabilities", [])
        except Exception as e:
            _LOGGER.debug("allow_capabilities error : " +
                          traceback.format_exc())
            return []

    @staticmethod
    def allow_capability(capability):
        return capability not in SettingManager().ignore_capabilities()

    @staticmethod
    def ignore_capability(capability):
        return capability in SettingManager().ignore_capabilities()
