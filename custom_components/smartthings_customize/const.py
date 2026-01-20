"""Constants used by the SmartThings component and platforms."""
from datetime import timedelta
import re

from homeassistant.const import Platform

DOMAIN = "smartthings_customize"

APP_OAUTH_CLIENT_NAME = "HA Customize"
APP_OAUTH_SCOPES = ["r:devices:*", "r:devices:*","w:devices:*","x:devices:*","l:devices","r:locations:*", "w:locations:*", "x:locations:*","r:scenes:*", "x:scenes:*", "r:installedapps:*", "l:installedapps", "w:installedapps"]
APP_NAME_PREFIX = "ha_customize."

CONF_APP_ID = "app_id"
CONF_CLOUDHOOK_URL = "cloudhook_url"
CONF_INSTALLED_APP_ID = "installed_app_id"
CONF_INSTANCE_ID = "instance_id"
CONF_LOCATION_ID = "location_id"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN = "token"

CONF_RESETTING_ENTITIES = "resetting_entities"
#CONF_ENABLE_DEFAULT_ENTITIES = "enable_default_entities"
CONF_ENABLE_SYNTAX_PROPERTY = "enable_syntax_property"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 5

DATA_MANAGER = "manager"
DATA_BROKERS = "brokers"
EVENT_BUTTON = "smartthings_customize.button"

SIGNAL_SMARTTHINGS_UPDATE = "smartthings_customize_update"
SIGNAL_SMARTAPP_PREFIX = "smartthings_customize_smartap_"

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
CONF_OPTIONS = "options"

CONF_DEFAULT_UNIT = "default_unit"
CONF_DEVICE_CLASS = "device_class"
CONF_STATE_CLASS = "state_class"
CONF_ENTITY_CATEGORY = "entity_category"

CONF_STATE = "state"

CONF_LAST_TIMESTAMP = "last_timestamp"

CAPA_SWITCH = "switch"

ATTR_SYNTAX = "syntax"

ON_STATE = "on_state"

CONF_STATE_MAPPING = "s2h_state_mapping"
CONF_MODE_MAPPING = "s2h_mode_mapping"
CONF_ACTION_MAPPING = "s2h_action_mapping"

CONF_SPEED_LIST = "speed_list"

DEFAULT = "default"

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
    Platform.VACUUM,
    Platform.VALVE,
    Platform.UPDATE,
]

IGNORED_CAPABILITIES = [
    "execute",
    "healthCheck",
    "ocf",
]

TOKEN_REFRESH_INTERVAL = timedelta(hours=12)

VAL_UID = "^(?:([0-9a-fA-F]{32})|([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}))$"
VAL_UID_MATCHER = re.compile(VAL_UID)

DEFAULT_UNIQUE_ID_FORMAT = "st_custom_%{device_id}_%{device_type}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"
DEFAULT_ENTITY_ID_FORMAT = "st_custom_%{device_id}_%{device_type}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"
