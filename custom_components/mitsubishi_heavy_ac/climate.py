"""Climate platform for Mitsubishi Heavy AC integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    ClimateEntityFeature, HVACMode,
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    SWING_OFF, SWING_ON,
)
from homeassistant.const import (
    CONF_NAME, STATE_ON, STATE_OFF, STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_TEMPERATURE,
    PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE, UnitOfTemperature
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

# Constants that were previously in const.py
DOMAIN = "mitsubishi_heavy_ac"
DEFAULT_NAME = "Mitsubishi Heavy AC"

CONF_UNIQUE_ID = 'unique_id'
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_REMOTE = "remote"

_LOGGER = logging.getLogger(__name__)

# Example device data - this would typically come from a JSON file or other configuration
# In a real implementation, this could be expanded to include different models or customization options
DEVICE_DATA = {
    "srk-zsx": {
        "name": "Mitsubishi Heavy SRK-ZSX",
        "min_temp": 16,
        "max_temp": 30,
        "precision": 1.0,
        "hvac_modes": [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.DRY, HVACMode.FAN_ONLY],
        "fan_modes": [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
        "swing_modes": [SWING_OFF, SWING_ON],
        "commands": {
            # Example IR/RF commands for various operations - these would be the actual codes for your remote
            "off": "OFF_COMMAND",
            "heat": {
                "16": "HEAT_16_COMMAND",
                "17": "HEAT_17_COMMAND",
                "18": "HEAT_18_COMMAND",
                "19": "HEAT_19_COMMAND",
                "20": "HEAT_20_COMMAND",
                "21": "HEAT_21_COMMAND",
                "22": "HEAT_22_COMMAND",
                "23": "HEAT_23_COMMAND",
                "24": "HEAT_24_COMMAND",
                "25": "HEAT_25_COMMAND",
                "26": "HEAT_26_COMMAND",
                "27": "HEAT_27_COMMAND",
                "28": "HEAT_28_COMMAND",
                "29": "HEAT_29_COMMAND",
                "30": "HEAT_30_COMMAND"
            },
            "cool": {
                "16": "COOL_16_COMMAND",
                "17": "COOL_17_COMMAND",
                "18": "COOL_18_COMMAND",
                "19": "COOL_19_COMMAND",
                "20": "COOL_20_COMMAND",
                "21": "COOL_21_COMMAND",
                "22": "COOL_22_COMMAND",
                "23": "COOL_23_COMMAND",
                "24": "COOL_24_COMMAND",
                "25": "COOL_25_COMMAND",
                "26": "COOL_26_COMMAND",
                "27": "COOL_27_COMMAND",
                "28": "COOL_28_COMMAND",
                "29": "COOL_29_COMMAND",
                "30": "COOL_30_COMMAND"
            },
            "auto": {
                "16": "AUTO_16_COMMAND",
                # ... more commands
            },
            "dry": {
                "16": "DRY_16_COMMAND",
                # ... more commands
            },
            "fan_only": "FAN_ONLY_COMMAND",
            "fan_modes": {
                "auto": "FAN_AUTO_COMMAND",
                "low": "FAN_LOW_COMMAND",
                "medium": "FAN_MEDIUM_COMMAND",
                "high": "FAN_HIGH_COMMAND"
            },
            "swing_modes": {
                "off": "SWING_OFF_COMMAND",
                "on": "SWING_ON_COMMAND"
            }
        }
    },
    "srk-zsp": {
        "name": "Mitsubishi Heavy SRK-ZSP",
        "min_temp": 18,
        "max_temp": 30,
        "precision": 1.0,
        "hvac_modes": [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.DRY],
        "fan_modes": [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH],
        "swing_modes": [SWING_OFF, SWING_ON],
        "commands": {
            # Similar command structure but with different codes
        }
    }
}

# Default model to use if not specified
DEFAULT_MODEL = "srk-zsx"

# Platform schema for direct climate configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_REMOTE): cv.entity_id,
    vol.Optional(CONF_TEMPERATURE_SENSOR): cv.entity_id,
    vol.Optional(CONF_HUMIDITY_SENSOR): cv.entity_id,
    vol.Optional("model", default=DEFAULT_MODEL): cv.string,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Mitsubishi Heavy AC platform from config."""
    # Get configuration values
    unique_id = config.get(CONF_UNIQUE_ID)
    model = config.get("model", DEFAULT_MODEL)
    remote = config.get(CONF_REMOTE)
    temp_sensor = config.get(CONF_TEMPERATURE_SENSOR)
    humidity_sensor = config.get(CONF_HUMIDITY_SENSOR)
    
    # Get device data for the specified model, or use default if not found
    device_data = DEVICE_DATA.get(model, DEVICE_DATA[DEFAULT_MODEL])
    
    # Use configured name or fall back to device data name
    name = config.get(CONF_NAME, device_data["name"])
    
    _LOGGER.debug(f"Setting up Mitsubishi Heavy AC with model: {model}, name: {name}")
    
    async_add_entities([
        MitsubishiHeavyClimate(
            hass, name, unique_id, device_data, remote, temp_sensor, humidity_sensor
        )
    ])

class MitsubishiHeavyClimate(ClimateEntity, RestoreEntity):
    """Representation of a Mitsubishi Heavy AC unit."""

    def __init__(
        self,
        hass,
        name,
        unique_id,
        device_data,
        remote=None,
        temperature_sensor=None,
        humidity_sensor=None
    ):
        """Initialize the climate device."""
        self.hass = hass
        self._name = name
        self._unique_id = unique_id
        self._device_data = device_data  # Store device data for reference
        self._remote = remote
        self._temperature_sensor_entity_id = temperature_sensor
        self._humidity_sensor_entity_id = humidity_sensor
        
        # Load device specific configurations from device_data
        self._min_temp = device_data["min_temp"]
        self._max_temp = device_data["max_temp"]
        self._precision = device_data["precision"]
        
        self._hvac_mode = HVACMode.OFF
        self._current_temperature = None
        self._current_humidity = None
        self._target_temperature = 22  # Default target temperature
        self._fan_mode = FAN_AUTO
        self._swing_mode = SWING_OFF
        
        # Load available modes from device data
        self._hvac_modes = device_data["hvac_modes"]
        self._fan_modes = device_data["fan_modes"]
        self._swing_modes = device_data["swing_modes"]
        
        # Store commands for controlling the AC
        self._commands = device_data["commands"]
    
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        
        # Add temperature sensor state listener if configured
        if self._temperature_sensor_entity_id:
            self.hass.helpers.event.async_track_state_change(
                self._temperature_sensor_entity_id, 
                self._async_temperature_sensor_changed
            )

        # Add humidity sensor state listener if configured
        if self._humidity_sensor_entity_id:
            self.hass.helpers.event.async_track_state_change(
                self._humidity_sensor_entity_id, 
                self._async_humidity_sensor_changed
            )
            
        # Update temperature and humidity from sensors if available
        await self._async_update_sensors()
        
        # Restore previous state if available
        last_state = await self.async_get_last_state()
        
        if last_state is not None:
            self._hvac_mode = last_state.state
            
            last_attributes = last_state.attributes
            self._target_temperature = last_attributes.get(ATTR_TEMPERATURE, self._target_temperature)
            self._fan_mode = last_attributes.get('fan_mode', self._fan_mode)
            self._swing_mode = last_attributes.get('swing_mode', self._swing_mode)
    
    async def _async_update_sensors(self):
        """Update temperature and humidity from sensors if available."""
        if self._temperature_sensor_entity_id:
            temp_state = self.hass.states.get(self._temperature_sensor_entity_id)
            if temp_state and temp_state.state not in (None, 'unknown', 'unavailable'):
                try:
                    self._current_temperature = float(temp_state.state)
                except ValueError:
                    _LOGGER.error("Unable to update from temperature sensor: %s", temp_state.state)
        
        if self._humidity_sensor_entity_id:
            humidity_state = self.hass.states.get(self._humidity_sensor_entity_id)
            if humidity_state and humidity_state.state not in (None, 'unknown', 'unavailable'):
                try:
                    self._current_humidity = float(humidity_state.state)
                except ValueError:
                    _LOGGER.error("Unable to update from humidity sensor: %s", humidity_state.state)
    
    async def _async_temperature_sensor_changed(self, entity_id, old_state, new_state):
        """Handle temperature sensor state changes."""
        if new_state is None or new_state.state in ('unavailable', 'unknown'):
            return
            
        try:
            self._current_temperature = float(new_state.state)
            self.async_write_ha_state()
        except ValueError:
            _LOGGER.error("Unable to update from temperature sensor: %s", new_state.state)
    
    async def _async_humidity_sensor_changed(self, entity_id, old_state, new_state):
        """Handle humidity sensor state changes."""
        if new_state is None or new_state.state in ('unavailable', 'unknown'):
            return
            
        try:
            self._current_humidity = float(new_state.state)
            self.async_write_ha_state()
        except ValueError:
            _LOGGER.error("Unable to update from humidity sensor: %s", new_state.state)
    
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name
    
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id
    
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS
    
    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity
    
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp
        
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp
    
    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._precision
    
    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._hvac_modes
    
    @property
    def hvac_mode(self):
        """Return current operation mode."""
        return self._hvac_mode
    
    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return self._fan_modes
    
    @property
    def fan_mode(self):
        """Return the fan mode."""
        return self._fan_mode
    
    @property
    def swing_modes(self):
        """Return the swing modes currently supported."""
        return self._swing_modes
    
    @property
    def swing_mode(self):
        """Return the current swing mode."""
        return self._swing_mode
    
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature
    
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE
        )
    
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._hvac_mode = hvac_mode
        
        # Send command through the configured remote
        if self._remote:
            command = None
            
            # Get the appropriate command based on the mode and temperature
            if hvac_mode == HVACMode.OFF:
                command = self._commands.get("off")
            elif hvac_mode in (HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.DRY):
                # Get the command for the current mode and temperature
                mode_commands = self._commands.get(hvac_mode.lower(), {})
                temp_str = str(int(self._target_temperature))
                command = mode_commands.get(temp_str)
            elif hvac_mode == HVACMode.FAN_ONLY:
                command = self._commands.get("fan_only")
                
            if command:
                _LOGGER.debug(f"Sending command: {command} via remote: {self._remote}")
                service_data = {
                    "entity_id": self._remote,
                    "command": command
                }
                await self.hass.services.async_call(
                    "remote", "send_command", service_data
                )
            else:
                _LOGGER.error(f"No command found for mode: {hvac_mode} at temp: {self._target_temperature}")
            
        await self.async_update_ha_state()
    
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._target_temperature = kwargs[ATTR_TEMPERATURE]
            
            # If the unit is on, send the command for the new temperature
            if self._hvac_mode != HVACMode.OFF and self._remote:
                mode_commands = self._commands.get(self._hvac_mode.lower(), {})
                temp_str = str(int(self._target_temperature))
                command = mode_commands.get(temp_str)
                
                if command:
                    _LOGGER.debug(f"Sending temperature command: {command}")
                    service_data = {
                        "entity_id": self._remote,
                        "command": command
                    }
                    await self.hass.services.async_call(
                        "remote", "send_command", service_data
                    )
                else:
                    _LOGGER.error(f"No command found for mode: {self._hvac_mode} at temp: {self._target_temperature}")
                    
            await self.async_update_ha_state()
    
    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fan_mode = fan_mode
        
        # Send fan mode command if remote is configured
        if self._remote:
            fan_commands = self._commands.get("fan_modes", {})
            command = fan_commands.get(fan_mode.lower())
            
            if command:
                _LOGGER.debug(f"Sending fan mode command: {command}")
                service_data = {
                    "entity_id": self._remote,
                    "command": command
                }
                await self.hass.services.async_call(
                    "remote", "send_command", service_data
                )
            else:
                _LOGGER.error(f"No command found for fan mode: {fan_mode}")
                
        await self.async_update_ha_state()
    
    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        self._swing_mode = swing_mode
        
        # Send swing mode command if remote is configured
        if self._remote:
            swing_commands = self._commands.get("swing_modes", {})
            command = swing_commands.get(swing_mode.lower())
            
            if command:
                _LOGGER.debug(f"Sending swing mode command: {command}")
                service_data = {
                    "entity_id": self._remote,
                    "command": command
                }
                await self.hass.services.async_call(
                    "remote", "send_command", service_data
                )
            else:
                _LOGGER.error(f"No command found for swing mode: {swing_mode}")
                
        await self.async_update_ha_state()