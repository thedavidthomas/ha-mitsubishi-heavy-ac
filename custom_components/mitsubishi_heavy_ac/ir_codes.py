"""IR code generation for Mitsubishi Heavy Industries SRK-ZSA series AC."""
import logging
from enum import IntEnum

_LOGGER = logging.getLogger(__name__)

# Constants based on MitsubishiHeavyZSHeatpumpIR.cpp
class Mode(IntEnum):
    """AC operation modes."""
    HEAT = 1
    COOL = 3
    DRY = 5
    FAN = 7
    AUTO = 8

class FanSpeed(IntEnum):
    """Fan speed."""
    AUTO = 0
    LOW = 1
    MEDIUM = 2
    MEDIUM_HIGH = 3
    HIGH = 4
    QUIET = 5
    STRONG = 6

class VSwing(IntEnum):
    """Vertical swing position."""
    STOPPED = 0      # Previously AUTO
    FIXED_TOP = 1    # Previously UP
    FIXED_MIDDLE_TOP = 2    # Previously MUP
    FIXED_MIDDLE = 3    # Previously MIDDLE
    FIXED_MIDDLE_BOTTOM = 4    # Previously MDOWN
    FIXED_BOTTOM = 5    # Previously DOWN
    RANGE_FULL = 6    # New option

class HSwing(IntEnum):
    """Horizontal swing position."""
    STOPPED = 0
    FIXED_LEFT = 1
    FIXED_CENTER_LEFT = 2
    FIXED_CENTER = 3
    FIXED_CENTER_RIGHT = 4
    FIXED_RIGHT = 5
    FIXED_LEFT_RIGHT = 6
    RANGE_CENTER = 7
    RANGE_FULL = 8

class Power(IntEnum):
    """Power settings."""
    OFF = 0
    ON = 1

def create_mitsubishi_heavy_zs_code(power, mode, fan_speed, temp, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):
    """Create IR code for Mitsubishi Heavy ZS series AC."""
    # Based on MitsubishiHeavyZSHeatpumpIR.cpp send method'fixedMiddleTop': VSwing.FIXED_MIDDLE_TOP,
    XED_MIDDLE,
    # Initialize data arraystom': VSwing.FIXED_MIDDLE_BOTTOM,
    data = [0] * 19'fixedBottom': VSwing.FIXED_BOTTOM,
    : VSwing.RANGE_FULL,
    # Constants
    if mode == Mode.HEAT:
        temp_mode = 0_zs_code(power, mode, fan_speed, temp, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    elif mode == Mode.COOL: for Mitsubishi Heavy ZS series AC."""
        temp_mode = 1ed on MitsubishiHeavyZSHeatpumpIR.cpp send method
    else:
        temp_mode = 0# Initialize data arrays
    
    # Header bits for the data
    data[0] = 0x52
    data[1] = 0xAEe.HEAT:
    data[2] = 0xC3= 0
    data[3] = 0x26ode.COOL:
    data[4] = 0xD9    temp_mode = 1
    
    # Set temperature (encode between 17-31°C)
    temperature = max(17, min(31, int(temp)))
     bits for the data
    # Byte 5
    data[5] = 0x11data[1] = 0xAE
    
    # Byte 6 - Temperature might start at bit 5
    data[6] = ((((temperature - 17) & 0x0F) << 4) | 0x00)data[4] = 0xD9
    
    # Special handling for QUIET and STRONG fan modeseen 17-31°C)
    adjusted_fan_speed = fan_speednt(temp)))
    if fan_speed == FanSpeed.QUIET:
        # QUIET mode uses special encoding - typically a combination of fan level and a special bit
        adjusted_fan_speed = FanSpeed.LOW  # Base is low speed
        # Set quiet mode bit in byte 15
        data[15] = 0x01 at bit 5
    elif fan_speed == FanSpeed.STRONG: << 4) | 0x00)
        # STRONG mode uses special encoding
        adjusted_fan_speed = FanSpeed.HIGH  # Base is high speedONG fan modes
        # Set strong mode bit in byte 15= fan_speed
        data[15] = 0x02n_speed == FanSpeed.QUIET:
    else: typically a combination of fan level and a special bit
        data[15] = 0x00  # Normal power mode    adjusted_fan_speed = FanSpeed.LOW  # Base is low speed
    yte 15
    # Byte 7 - Mode and fan speed
    data[7] = (int(mode) << 5) | int(adjusted_fan_speed)elif fan_speed == FanSpeed.STRONG:
    ecial encoding
    # Byte 8 - Vertical swingnSpeed.HIGH  # Base is high speed
    data[8] = int(v_swing) << 5    # Set strong mode bit in byte 15
    
    # Byte 9 - Horizontal swing
    data[9] = int(h_swing) << 5    data[15] = 0x00  # Normal power mode
    
    # Byte 10 - On/Offeed
    data[10] = int(power) << 5data[7] = (int(mode) << 5) | int(adjusted_fan_speed)
    
    # Calculate checksums
    data[11] = ((data[5] + data[6] + data[7]) & 0xFF)
    data[12] = ((data[8] + data[9]) & 0xFF)
    data[16] = 0x00# Byte 9 - Horizontal swing
    
    # Convert to HEX string for Broadlink format
    hex_codes = []
    for i in range(19):  # Changed to 19 bytes based on ZS model << 5
        if i < len(data):
            hex_codes.append(f"{data[i]:02X}")te checksums
        else: + data[7]) & 0xFF)
            hex_codes.append("00")data[12] = ((data[8] + data[9]) & 0xFF)
    
    # Broadlink packets need to be in lowercase
    hex_string = ''.join(hex_codes).lower()# Convert to HEX string for Broadlink format
    
    return hex_string    for i in range(19):  # Changed to 19 bytes based on ZS model
en(data):
# Helper methods
def get_heat_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):
    """Get IR code for heat mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.HEAT, fan_speed, temp, v_swing, h_swing)    

def get_cool_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):lower()
    """Get IR code for cool mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.COOL, fan_speed, temp, v_swing, h_swing)    return hex_string

def get_dry_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):
    """Get IR code for dry mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.DRY, fan_speed, temp, v_swing, h_swing)    """Get IR code for heat mode."""
wing, h_swing)
def get_fan_code(fan_speed=FanSpeed.AUTO, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):
    """Get IR code for fan mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.FAN, fan_speed, 22, v_swing, h_swing)    """Get IR code for cool mode."""
ing)
def get_auto_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.STOPPED, h_swing=HSwing.AUTO):
    """Get IR code for auto mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.AUTO, fan_speed, temp, v_swing, h_swing)    """Get IR code for dry mode."""
itsubishi_heavy_zs_code(Power.ON, Mode.DRY, fan_speed, temp, v_swing, h_swing)
def get_off_code():
    """Get IR code for power off.""":

    return create_mitsubishi_heavy_zs_code(Power.OFF, Mode.COOL, FanSpeed.AUTO, 22)    """Get IR code for fan mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.FAN, fan_speed, 22, v_swing, h_swing)

def get_auto_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for auto mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.AUTO, fan_speed, temp, v_swing, h_swing)

def get_off_code():
    """Get IR code for power off."""
    return create_mitsubishi_heavy_zs_code(Power.OFF, Mode.COOL, FanSpeed.AUTO, 22)