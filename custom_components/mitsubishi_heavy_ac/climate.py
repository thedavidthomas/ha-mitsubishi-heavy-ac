"""Climate platform for Mitsubishi Heavy AC integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    SWING_OFF, SWING_ON,
)
from homeassistant.const import (
    CONF_NAME, CONF_UNIQUE_ID, CONF_REMOTE, UnitOfTemperature, STATE_OFF, STATE_ON,
    ATTR_TEMPERATURE, Platform
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN, 
    CONF_TEMPERATURE_SENSOR, 
    CONF_HUMIDITY_SENSOR,
    DEFAULT_NAME
)

_LOGGER = logging.getLogger(__name__)

# Platform schema for direct climate configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_REMOTE): cv.entity_id,
    vol.Optional(CONF_TEMPERATURE_SENSOR): cv.entity_id,
    vol.Optional(CONF_HUMIDITY_SENSOR): cv.entity_id,
})

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Mitsubishi Heavy AC platform from config."""
    # Create climate entity from direct configuration
    name = config.get(CONF_NAME, DEFAULT_NAME)
    unique_id = config.get(CONF_UNIQUE_ID)
    remote = config.get(CONF_REMOTE)
    temp_sensor = config.get(CONF_TEMPERATURE_SENSOR)
    humidity_sensor = config.get(CONF_HUMIDITY_SENSOR)
    
    async_add_entities([
        MitsubishiHeavyClimate(
            hass, 
            name, 
            unique_id, 
            remote, 
            temp_sensor, 
            humidity_sensor
        )
    ])

class MitsubishiHeavyClimate(ClimateEntity, RestoreEntity):
    """Representation of a Mitsubishi Heavy AC unit."""

    def __init__(
        self,
        hass,
        name,
        unique_id,
        remote=None,
        temperature_sensor=None,
        humidity_sensor=None
    ):
        """Initialize the climate device."""
        self.hass = hass
        self._name = name
        self._unique_id = unique_id
        self._remote = remote
        self._temperature_sensor_entity_id = temperature_sensor
        self._humidity_sensor_entity_id = humidity_sensor
        
        # Load device specific configurations
        self._min_temp = 16
        self._max_temp = 30
        self._precision = 1.0
        
        self._hvac_mode = HVACMode.OFF
        self._current_temperature = None
        self._current_humidity = None
        self._target_temperature = 22
        self._fan_mode = FAN_AUTO
        self._swing_mode = SWING_OFF
        
        # Load available modes
        self._hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO, HVACMode.DRY, HVACMode.FAN_ONLY]
        self._fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
        self._swing_modes = [SWING_OFF, SWING_ON]
    
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
            # Example of a service call to a Broadlink RM device
            # You'll need to modify this to fit your specific remote control solution
            service_data = {
                "entity_id": self._remote,
                "command": f"{hvac_mode.lower()}_{int(self._target_temperature)}"
            }
            await self.hass.services.async_call(
                "remote", "send_command", service_data
            )
            
        await self.async_update_ha_state()
    
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._target_temperature = kwargs[ATTR_TEMPERATURE]
            # Add your code to send commands to the AC unit
            await self.async_update_ha_state()
    
    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fan_mode = fan_mode
        # Add your code to send commands to the AC unit
        await self.async_update_ha_state()
    
    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        self._swing_mode = swing_mode
        # Add your code to send commands to the AC unit
        await self.async_update_ha_state()