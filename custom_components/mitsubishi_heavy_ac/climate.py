"""Climate platform for Mitsubishi Heavy AC integration."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    SWING_OFF, SWING_ON,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitsubishi Heavy AC climate from a config entry."""
    async_add_entities([MitsubishiHeavyClimate()])

class MitsubishiHeavyClimate(ClimateEntity):
    """Representation of a Mitsubishi Heavy AC unit."""

    _attr_has_entity_name = True
    _attr_name = "Mitsubishi Heavy AC"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_ON]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
    )

    def __init__(self) -> None:
        """Initialize the climate device."""
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = None
        self._attr_target_temperature = 22
        self._attr_fan_mode = FAN_AUTO
        self._attr_swing_mode = SWING_OFF