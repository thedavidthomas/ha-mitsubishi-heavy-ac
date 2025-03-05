"""Constants for the Mitsubishi Heavy AC integration."""
from typing import Final

DOMAIN: Final = "mitsubishi_heavy_ac"
DEFAULT_NAME: Final = "Mitsubishi Heavy AC"
CONF_MIN_TEMP: Final = "min_temp"
CONF_MAX_TEMP: Final = "max_temp"
CONF_REMOTE: Final = "remote"

# Configuration options
CONF_TEMPERATURE_SENSOR: Final = "temperature_sensor"
CONF_HUMIDITY_SENSOR: Final = "humidity_sensor"

# Valid configuration keys
VALID_CONFIG_KEYS: Final = {
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_REMOTE,
}
