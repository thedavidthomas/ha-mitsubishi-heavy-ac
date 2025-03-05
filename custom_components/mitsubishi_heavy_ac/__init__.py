"""The Mitsubishi Heavy AC integration."""
from __future__ import annotations

import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Mitsubishi Heavy AC component."""
    # Just return True as all setup is handled by the platform
    return True