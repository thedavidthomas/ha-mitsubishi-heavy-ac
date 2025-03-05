"""Climate platform for Mitsubishi Heavy Industries AC."""
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    SWING_OFF,
    SWING_ON,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_HOST,
    CONF_MAC,
    CONF_TIMEOUT,
    UnitOfTemperature,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.core import callback

# Remove legacy constants mapping and use HVACMode enum directly throughout the code

from .const import (
    DOMAIN,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
)
from .ir_codes import (
    get_heat_code,
    get_cool_code,
    get_dry_code,
    get_fan_code,
    get_auto_code,
    get_off_code,
    FanSpeed,
    VSwing,
    HSwing,
    Light,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

# Add new constants for sensor entities
CONF_REMOTE_ENTITY_ID = "remote_entity_id"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"

# Update schema to support both configuration methods
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_MAC): cv.string,
    vol.Optional(CONF_REMOTE_ENTITY_ID): cv.entity_id,
    vol.Optional(CONF_TEMPERATURE_SENSOR): cv.entity_id,
    vol.Optional(CONF_HUMIDITY_SENSOR): cv.entity_id,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_MIN_TEMP, default=17): vol.Coerce(int),
    vol.Optional(CONF_MAX_TEMP, default=30): vol.Coerce(int),
})

# Add validation to ensure either remote_entity_id OR (host AND mac) are provided
PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA,
    vol.Any(
        vol.Schema({
            vol.Required(CONF_REMOTE_ENTITY_ID): cv.entity_id,
            vol.Optional(CONF_HOST): cv.string,
            vol.Optional(CONF_MAC): cv.string,
            # ...other fields...
        }),
        vol.Schema({
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_MAC): cv.string,
            vol.Optional(CONF_REMOTE_ENTITY_ID): cv.entity_id,
            # ...other fields...
        })
    )
)

# Update support flags to use the new ClimateEntityFeature enum
SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE |
    ClimateEntityFeature.FAN_MODE |
    ClimateEntityFeature.SWING_MODE
)

HA_FAN_TO_MHI = {
    'auto': FanSpeed.AUTO,
    'quiet': FanSpeed.QUIET,
    'low': FanSpeed.LOW,
    'medium': FanSpeed.MEDIUM,
    'medium_high': FanSpeed.MEDIUM_HIGH,
    'high': FanSpeed.HIGH,
    'strong': FanSpeed.STRONG,
}

MHI_FAN_TO_HA = {v: k for k, v in HA_FAN_TO_MHI.items()}

HA_SWING_TO_MHI_V = {
    'auto_vertical': VSwing.AUTO,
    'up': VSwing.UP,
    'middle_up': VSwing.MUP,
    'middle': VSwing.MIDDLE,
    'middle_down': VSwing.MDOWN,
    'down': VSwing.DOWN,
}

HA_SWING_TO_MHI_H = {
    'stopped': HSwing.STOPPED,
    'fixedLeft': HSwing.FIXED_LEFT,
    'fixedCenterLeft': HSwing.FIXED_CENTER_LEFT,
    'fixedCenter': HSwing.FIXED_CENTER,
    'fixedCenterRight': HSwing.FIXED_CENTER_RIGHT,
    'fixedRight': HSwing.FIXED_RIGHT,
    'fixedLeftRight': HSwing.FIXED_LEFT_RIGHT,
    'rangeCenter': HSwing.RANGE_CENTER,
    'rangeFull': HSwing.RANGE_FULL,
}

# Combined swing modes for both vertical and horizontal
HA_SWING_TO_MHI = {**HA_SWING_TO_MHI_V, **HA_SWING_TO_MHI_H}

MHI_SWING_TO_HA = {v: k for k, v in HA_SWING_TO_MHI.items()}

# Update HVAC mode mapping to use HVACMode directly
HA_HVAC_TO_MHI_FUNCTION = {
    HVACMode.AUTO: get_auto_code,
    HVACMode.COOL: get_cool_code,
    HVACMode.DRY: get_dry_code,
    HVACMode.FAN_ONLY: get_fan_code,
    HVACMode.HEAT: get_heat_code,
    HVACMode.OFF: get_off_code,
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Mitsubishi Heavy Industries AC platform."""
    name = config[CONF_NAME]
    timeout = config[CONF_TIMEOUT]
    min_temp = config[CONF_MIN_TEMP]
    max_temp = config[CONF_MAX_TEMP]
    
    # Get optional sensor entity IDs
    temperature_sensor = config.get(CONF_TEMPERATURE_SENSOR)
    humidity_sensor = config.get(CONF_HUMIDITY_SENSOR)
    
    # Get Broadlink device either via remote entity ID or direct IP/MAC
    broadlink_device = None
    
    if CONF_REMOTE_ENTITY_ID in config:
        remote_entity_id = config[CONF_REMOTE_ENTITY_ID]
        
        # Get the remote entity state
        remote = hass.states.get(remote_entity_id)
        if not remote:
            _LOGGER.error("Remote entity %s not found", remote_entity_id)
            return
        
        # Get the device reference from entity registry
        from homeassistant.helpers.entity_registry import async_get
        entity_registry = async_get(hass)
        entity_entry = entity_registry.async_get(remote_entity_id)
        
        if not entity_entry:
            _LOGGER.error("Could not find entity registry entry for %s", remote_entity_id)
            return
            
        # Get the Broadlink device from the remote entity
        from homeassistant.helpers.device_registry import async_get as async_get_device_registry
        device_registry = async_get_device_registry(hass)
        device_entry = device_registry.async_get(entity_entry.device_id)
        
        if not device_entry:
            _LOGGER.error("Could not find device for entity %s", remote_entity_id)
            return
            
        # Get the actual device
        from homeassistant.components.remote import RemoteEntity
        
        # Access remote entity from entity registry
        try:
            remote_entity = hass.data.get("entity_components", {}).get("remote", {}).get_entity(remote_entity_id)
            if hasattr(remote_entity, "_device") and remote_entity._device:
                broadlink_device = remote_entity._device
            else:
                _LOGGER.error("Could not access Broadlink device from remote entity %s", remote_entity_id)
                return
        except Exception as e:
            _LOGGER.error("Error accessing Broadlink device from remote entity: %s", str(e))
            return
    else:
        host = config[CONF_HOST]
        mac = config[CONF_MAC]
        try:
            broadlink_device = await get_broadlink_device(hass, host, mac)
            
            if not broadlink_device:
                _LOGGER.error("Failed to connect to Broadlink device at %s", host)
                return
            
            _LOGGER.info("Connected to Broadlink device at %s", host)
        except Exception as e:
            _LOGGER.error("Failed to initialize Broadlink device: %s", str(e))
            return

    # Create and add the entity
    try:
        async_add_entities([entity := MitsubishiHeavyAC(
            hass, name, broadlink_device, min_temp, max_temp,
            temperature_sensor, humidity_sensor
        )])
        
        # Register services
        async def async_light_on_service(service):
            """Handle light on service call."""
            await entity.async_set_light(True)
            await entity.async_update_ha_state()
        
        async def async_light_off_service(service):
            """Handle light off service call."""
            await entity.async_set_light(False)
            await entity.async_update_ha_state()
        
        hass.services.async_register(
            DOMAIN, 'set_light_on', async_light_on_service
        )
        
        hass.services.async_register(
            DOMAIN, 'set_light_off', async_light_off_service
        )
    except Exception as e:
        _LOGGER.error("Failed to set up climate entity: %s", str(e))
        return

class MitsubishiHeavyAC(ClimateEntity):
    """Representation of a Mitsubishi Heavy Industries AC."""

    def __init__(self, hass, name, broadlink_device, min_temp, max_temp,
                 temperature_sensor=None, humidity_sensor=None):
        """Initialize the climate device."""
        self.hass = hass
        self._name = name
        self._broadlink_device = broadlink_device
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._temperature_sensor = temperature_sensor
        self._humidity_sensor = humidity_sensor
        
        # Update default state to use HVACMode enum
        self._hvac_mode = HVACMode.OFF
        self._target_temperature = 22
        self._current_temperature = None
        self._current_humidity = None
        self._fan_mode = "auto"
        self._swing_mode = "auto_vertical"
        self._horizontal_swing = "stopped"  # Updated default from "auto_horizontal"
        self._available = True
        self._light = Light.ON  # Default state for light
        
    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        # Add state change listeners for temperature and humidity sensors
        if self._temperature_sensor:
            self._async_update_temp(self._temperature_sensor)
            self.async_on_remove(
                self.hass.helpers.event.async_track_state_change(
                    self._temperature_sensor, self._async_temp_sensor_changed
                )
            )
            
        if self._humidity_sensor:
            self._async_update_humidity(self._humidity_sensor)
            self.async_on_remove(
                self.hass.helpers.event.async_track_state_change(
                    self._humidity_sensor, self._async_humidity_sensor_changed
                )
            )
            
    @callback
    def _async_temp_sensor_changed(self, entity_id, old_state, new_state):
        """Handle temperature sensor state changes."""
        if new_state is None:
            return
        self._async_update_temp(entity_id)
        self.async_write_ha_state()

    @callback
    def _async_humidity_sensor_changed(self, entity_id, old_state, new_state):
        """Handle humidity sensor state changes."""
        if new_state is None:
            return
        self._async_update_humidity(entity_id)
        self.async_write_ha_state()

    @callback
    def _async_update_temp(self, entity_id):
        """Update thermostat with latest state from temperature sensor."""
        try:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state != "unknown" and state.state != "unavailable":
                self._current_temperature = float(state.state)
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Unable to update from temperature sensor: %s", ex)

    @callback
    def _async_update_humidity(self, entity_id):
        """Update thermostat with latest state from humidity sensor."""
        try:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state != "unknown" and state.state != "unavailable":
                self._current_humidity = float(state.state)
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Unable to update from humidity sensor: %s", ex)
    
    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name
        
    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
        
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS
        
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature
        
    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity
        
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature
        
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp
        
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp
        
    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        return self._hvac_mode
        
    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
        ]
        
    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._fan_mode
        
    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return list(HA_FAN_TO_MHI.keys())
        
    @property
    def swing_mode(self):
        """Return the swing mode."""
        return self._swing_mode
        
    @property
    def swing_modes(self):
        """Return the list of available swing modes."""
        return list(HA_SWING_TO_MHI.keys())
        
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS
        
    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            return
            
        self._target_temperature = kwargs[ATTR_TEMPERATURE]
        await self.send_command()
        self.async_write_ha_state()
            
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._hvac_mode = hvac_mode
        await self.send_command()
        self.async_write_ha_state()
            
    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fan_mode = fan_mode
        await self.send_command()
        self.async_write_ha_state()
            
    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        # Determine if this is a vertical or horizontal swing setting
        if swing_mode in HA_SWING_TO_MHI_V:
            self._swing_mode = swing_mode
        elif swing_mode in HA_SWING_TO_MHI_H:
            self._horizontal_swing = swing_mode
        else:
            _LOGGER.warning("Unsupported swing mode: %s", swing_mode)
            return
        
        await self.send_command()
        self.async_write_ha_state()
        
    async def async_turn_on(self):
        """Turn the entity on."""
        if self._hvac_mode == HVACMode.OFF:
            self._hvac_mode = HVACMode.COOL
        await self.send_command()
        self.async_write_ha_state()
        
    async def async_turn_off(self):
        """Turn the entity off."""
        self._hvac_mode = HVACMode.OFF
        await self.send_command()
        self.async_write_ha_state()
        
    async def async_set_light(self, light_on):
        """Set the display light on or off."""
        self._light = Light.ON if light_on else Light.OFF
        await self.send_command()
        self.async_write_ha_state()
        
    async def send_command(self):
        """Send IR command to device."""
        try:
            if self._hvac_mode == HVACMode.OFF:
                ir_code = get_off_code()
            else:
                ir_function = HA_HVAC_TO_MHI_FUNCTION[self._hvac_mode]
                fan_speed = HA_FAN_TO_MHI[self._fan_mode]
                
                # Get swing settings - default to appropriate values if not found
                v_swing = HA_SWING_TO_MHI_V.get(self._swing_mode, VSwing.AUTO)
                
                # Use STOPPED as default instead of AUTO for horizontal swing
                h_swing = HA_SWING_TO_MHI_H.get(self._horizontal_swing, HSwing.STOPPED)
                
                if self._hvac_mode == HVACMode.FAN_ONLY:
                    ir_code = ir_function(
                        fan_speed=fan_speed, 
                        v_swing=v_swing, 
                        h_swing=h_swing,
                        light=self._light
                    )
                else:
                    ir_code = ir_function(
                        temp=self._target_temperature,
                        fan_speed=fan_speed,
                        v_swing=v_swing,
                        h_swing=h_swing,
                        light=self._light
                    )
            
            # Convert hex string to bytes
            command = bytes.fromhex(ir_code)
            
            # Send command
            await self.hass.async_add_executor_job(
                self._broadlink_device.send_data, command
            )
            
            _LOGGER.debug(
                "Sent IR command for %s mode with temperature %s°C, fan %s, v_swing %s, h_swing %s, light %s",
                self._hvac_mode,
                self._target_temperature,
                self._fan_mode,
                self._swing_mode,
                self._horizontal_swing,
                "ON" if self._light == Light.ON else "OFF"
            )
            
            # Mark device as available after successful command
            self._available = True
            
        except Exception as e:
            self._available = False
            _LOGGER.error("Error sending command: %s", str(e))