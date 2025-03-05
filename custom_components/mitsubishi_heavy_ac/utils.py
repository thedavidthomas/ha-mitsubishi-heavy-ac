"""Utility functions for Mitsubishi Heavy Industries AC."""
import logging
import broadlink

_LOGGER = logging.getLogger(__name__)

async def get_broadlink_device(hass, host, mac):
    """Get a Broadlink device."""
    try:
        # Convert MAC string to bytes
        mac_addr = bytes.fromhex(mac.replace(':', ''))
        
        # Try to connect to the device
        device = broadlink.hello(host)
        if device is None:
            _LOGGER.error("Failed to connect to Broadlink device at %s", host)
            return None
            
        # Authenticate
        await hass.async_add_executor_job(device.auth)
        
        return device
    except Exception as e:
        _LOGGER.error("Failed to connect to Broadlink device: %s", str(e))
        return None
