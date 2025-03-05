"""Climate platform for Mitsubishi Heavy Industries AC."""
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.broadlink import async_get_device as get_broadlink_device
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_HOST,
    CONF_MAC,
    CONF_TIMEOUT,
    UnitOfTemperature,
)
import homeassistant.helpers.config_validation as cv

from . import DOMAIN
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
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Mitsubishi Heavy AC"
DEFAULT_TIMEOUT = 10
SCAN_INTERVAL = timedelta(seconds=60)

CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_MIN_TEMP, default=17): vol.Coerce(int),
    vol.Optional(CONF_MAX_TEMP, default=30): vol.Coerce(int),
})

SUPPORT_FLAGS = (
    SUPPORT_TARGET_TEMPERATURE |
    SUPPORT_FAN_MODE |
    SUPPORT_SWING_MODE
)

HA_FAN_TO_MHI = {
    'auto': FanSpeed.AUTO,
    'low': FanSpeed.SPEED_1,
    'medium': FanSpeed.SPEED_2,
    'high': FanSpeed.SPEED_3,
    'silent': FanSpeed.SILENT,
    'quiet': FanSpeed.QUIET,
}

MHI_FAN_TO_HA = {v: k for k, v in HA_FAN_TO_MHI.items()}

HA_SWING_TO_MHI = {
    'auto': VSwing.AUTO,
    'up': VSwing.UP,
    'middle-up': VSwing.MUP,
    'middle': VSwing.MIDDLE,
    'middle-down': VSwing.MDOWN,
    'down': VSwing.DOWN,
    'left': HSwing.LEFT,
    'middle-left': HSwing.MLEFT,
    'middle': HSwing.MIDDLE,
    'middle-right': HSwing.MRIGHT,
    'right': HSwing.RIGHT,
}

MHI_SWING_TO_HA = {v: k for k, v in HA_SWING_TO_MHI.items()}

HA_HVAC_TO_MHI_FUNCTION = {
    HVAC_MODE_AUTO: get_auto_code,
    HVAC_MODE_COOL: get_cool_code,
    HVAC_MODE_DRY: get_dry_code,
    HVAC_MODE_FAN_ONLY: get_fan_code,
    HVAC_MODE_HEAT: get_heat_code,
    HVAC_MODE_OFF: get_off_code,
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Mitsubishi Heavy Industries AC platform."""
    host = config[CONF_HOST]
    mac = config[CONF_MAC]
    name = config[CONF_NAME]
    timeout = config[CONF_TIMEOUT]
    min_temp = config[CONF_MIN_TEMP]
    max_temp = config[CONF_MAX_TEMP]

    try:
        broadlink_device = await get_broadlink_device(hass, host, mac)
        
        if not broadlink_device:
            _LOGGER.error("Failed to connect to Broadlink device at %s", host)
            return
        
        _LOGGER.info("Connected to Broadlink device at %s", host)
        
        async_add_entities([
            MitsubishiHeavyAC(
                hass, name, broadlink_device, min_temp, max_temp
            )
        ])
        
    except Exception as e:
        _LOGGER.error("Failed to initialize Broadlink device: %s", str(e))
        return

class MitsubishiHeavyAC(ClimateEntity):
    """Representation of a Mitsubishi Heavy Industries AC."""

    def __init__(self, hass, name, broadlink_device, min_temp, max_temp):
        """Initialize the climate device."""
        self.hass = hass
        self._name = name
        self._broadlink_device = broadlink_device
        self._min_temp = min_temp
        self._max_temp = max_temp
        
        # Default state
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temperature = 22
        self._current_temperature = None
        self._fan_mode = "auto"
        self._swing_mode = "auto"
        self._available = True
        
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
            HVAC_MODE_OFF,
            HVAC_MODE_AUTO,
            HVAC_MODE_COOL,
            HVAC_MODE_DRY,
            HVAC_MODE_FAN_ONLY,
            HVAC_MODE_HEAT,
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
            
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._hvac_mode = hvac_mode
        await self.send_command()
            
    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fan_mode = fan_mode
        await self.send_command()
            
    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        self._swing_mode = swing_mode
        await self.send_command()
        
    async def async_turn_on(self):
        """Turn the entity on."""
        if self._hvac_mode == HVAC_MODE_OFF:
            self._hvac_mode = HVAC_MODE_COOL
        await self.send_command()
        
    async def async_turn_off(self):
        """Turn the entity off."""
        self._hvac_mode = HVAC_MODE_OFF
        await self.send_command()
        
    async def send_command(self):
        """Send IR command to device."""
        try:
            if self._hvac_mode == HVAC_MODE_OFF:
                ir_code = get_off_code()
            else:
                ir_function = HA_HVAC_TO_MHI_FUNCTION[self._hvac_mode]
                fan_speed = HA_FAN_TO_MHI[self._fan_mode]
                v_swing = HA_SWING_TO_MHI[self._swing_mode]
                h_swing = HA_SWING_TO_MHI[self._swing_mode]
                
                if self._hvac_mode == HVAC_MODE_FAN_ONLY:
                    ir_code = ir_function(fan_speed=fan_speed, v_swing=v_swing, h_swing=h_swing)
                else:
                    ir_code = ir_function(
                        temp=self._target_temperature,
                        fan_speed=fan_speed,
                        v_swing=v_swing,
                        h_swing=h_swing
                    )
            
            # Convert hex string to bytes
            command = bytes.fromhex(ir_code)
            
            # Send command
            await self.hass.async_add_executor_job(
                self._broadlink_device.send_data, command
            )
            
            _LOGGER.debug(
                "Sent IR command for %s mode with temperature %s°C, fan %s, swing %s",
                self._hvac_mode,
                self._target_temperature,
                self._fan_mode,
                self._swing_mode
            )
            
        except Exception as e:
            self._available = False
            _LOGGER.error("Error sending command: %s", str(e))