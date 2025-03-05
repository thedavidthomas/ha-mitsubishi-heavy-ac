"""The Mitsubishi Heavy AC integration."""
from __future__ import annotations

import logging

# Domain definition moved to climate.py
DOMAIN = "mitsubishi_heavy_ac"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Mitsubishi Heavy AC component."""
    # Just return True as all setup is handled by the platform
    return True