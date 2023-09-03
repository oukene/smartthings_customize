"""Constants used by the SmartThings component and platforms."""
from datetime import timedelta
import re

from homeassistant.const import Platform

DOMAIN = "smartthings_customize"

APP_OAUTH_CLIENT_NAME = "HA Customize"
APP_OAUTH_SCOPES = ["r:devices:*"]
APP_NAME_PREFIX = "homeassistant."

CONF_APP_ID = "app_id"
CONF_CLOUDHOOK_URL = "cloudhook_url"
CONF_INSTALLED_APP_ID = "installed_app_id"
CONF_INSTANCE_ID = "instance_id"
CONF_LOCATION_ID = "location_id"
CONF_REFRESH_TOKEN = "refresh_token"

DATA_MANAGER = "manager"
DATA_BROKERS = "brokers"
EVENT_BUTTON = "smartthings.button"

SIGNAL_SMARTTHINGS_UPDATE = "smartthings_update"
SIGNAL_SMARTAPP_PREFIX = "smartthings_smartap_"

SETTINGS_INSTANCE_ID = "hassInstanceId"

SUBSCRIPTION_WARNING_LIMIT = 40

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

GLOBAL_SETTING = "globals"
DEVICE_SETTING = "devices"

CONF_NAME = "name"
CONF_COMPONENT = "component"
CONF_CAPABILITY = "capability"
CONF_ATTRIBUTE = "attribute"
CONF_COMMAND = "command"
CONF_ARGUMENT = "argument"
CONF_PARENT_ENTITY_ID = "parent_entity_id"
CONF_ENTITY_ID_FORMAT = "entity_id_format"

ATTR_SYNTAX = "syntax"

# Ordered 'specific to least-specific platform' in order for capabilities
# to be drawn-down and represented by the most appropriate platform.
PLATFORMS = [
    Platform.CLIMATE,
    Platform.FAN,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.COVER,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SCENE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.TEXT,
]

CUSTOM_PLATFORMS = {
    Platform.BINARY_SENSOR: "binary_sensors",
    Platform.SWITCH: "switches",
    Platform.SENSOR: "sensors",
    Platform.NUMBER: "numbers",
    Platform.SELECT: "selects",
    Platform.BUTTON: "buttons",
    Platform.TEXT: "texts",
    Platform.CLIMATE: "climates",
}

IGNORED_CAPABILITIES = [
    "execute",
    "healthCheck",
    "ocf",
]

TOKEN_REFRESH_INTERVAL = timedelta(days=14)

VAL_UID = "^(?:([0-9a-fA-F]{32})|([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}))$"
VAL_UID_MATCHER = re.compile(VAL_UID)

DEFAULT_ENTITY_ID_FORMAT = "st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"
