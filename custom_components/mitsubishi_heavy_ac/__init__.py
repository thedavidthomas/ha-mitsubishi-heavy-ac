"""Mitsubishi Heavy Industries AC integration."""
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mitsubishi_heavy_ac"

async def async_setup(hass, config):
    """Set up the Mitsubishi Heavy Industries AC component."""
    return True

async def async_setup_entry(hass, config_entry):
    """Set up from a config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "climate")
    )
    return True

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(config_entry, "climate")