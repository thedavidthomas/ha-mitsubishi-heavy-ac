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
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SILENT = 4  # Some models might not support this
    QUIET = 5  # Quiet mode

class VSwing(IntEnum):
    """Vertical swing position."""
    AUTO = 0
    UP = 1
    MUP = 2
    MIDDLE = 3
    MDOWN = 4
    DOWN = 5

class HSwing(IntEnum):
    """Horizontal swing position."""
    AUTO = 0
    LEFT = 1
    MLEFT = 2
    MIDDLE = 3
    MRIGHT = 4
    RIGHT = 5

class Power(IntEnum):
    """Power settings."""
    OFF = 0
    ON = 1

def create_mitsubishi_heavy_zs_code(power, mode, fan_speed, temp, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Create IR code for Mitsubishi Heavy ZS series AC."""
    # Based on MitsubishiHeavyZSHeatpumpIR.cpp send method
    
    # Initialize data arrays
    data = [0] * 19
    
    # Constants
    if mode == Mode.HEAT:
        temp_mode = 0
    elif mode == Mode.COOL:
        temp_mode = 1
    else:
        temp_mode = 0
    
    # Header bits for the data
    data[0] = 0x52
    data[1] = 0xAE
    data[2] = 0xC3
    data[3] = 0x26
    data[4] = 0xD9
    
    # Set temperature (encode between 17-31°C)
    temperature = max(17, min(31, int(temp)))
    
    # Byte 5
    data[5] = 0x11
    
    # Byte 6 - Temperature might start at bit 5
    data[6] = ((((temperature - 17) & 0x0F) << 4) | 0x00)
    
    # Byte 7 - Mode and fan speed
    data[7] = (int(mode) << 5) | int(fan_speed)
    
    # Byte 8 - Vertical swing
    data[8] = int(v_swing) << 5
    
    # Byte 9 - Horizontal swing
    data[9] = int(h_swing) << 5
    
    # Byte 10 - On/Off
    data[10] = int(power) << 5
    
    # Byte 15 - Power mode (normal)
    data[15] = 0x00
    
    # Calculate checksums
    data[11] = ((data[5] + data[6] + data[7]) & 0xFF)
    data[12] = ((data[8] + data[9]) & 0xFF)
    data[16] = 0x00
    
    # Convert to HEX string for Broadlink format
    hex_codes = []
    for i in range(19):  # Changed to 19 bytes based on ZS model
        if i < len(data):
            hex_codes.append(f"{data[i]:02X}")
        else:
            hex_codes.append("00")
    
    # Broadlink packets need to be in lowercase
    hex_string = ''.join(hex_codes).lower()
    
    return hex_string

# Helper methods
def get_heat_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for heat mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.HEAT, fan_speed, temp, v_swing, h_swing)

def get_cool_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for cool mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.COOL, fan_speed, temp, v_swing, h_swing)

def get_dry_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for dry mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.DRY, fan_speed, temp, v_swing, h_swing)

def get_fan_code(fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for fan mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.FAN, fan_speed, 22, v_swing, h_swing)

def get_auto_code(temp=22, fan_speed=FanSpeed.AUTO, v_swing=VSwing.AUTO, h_swing=HSwing.AUTO):
    """Get IR code for auto mode."""
    return create_mitsubishi_heavy_zs_code(Power.ON, Mode.AUTO, fan_speed, temp, v_swing, h_swing)

def get_off_code():
    """Get IR code for power off."""
    return create_mitsubishi_heavy_zs_code(Power.OFF, Mode.COOL, FanSpeed.AUTO, 22)