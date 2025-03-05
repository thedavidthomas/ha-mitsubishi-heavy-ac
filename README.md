# Mitsubishi Heavy Industries Air Conditioner for Home Assistant

This custom component allows controlling Mitsubishi Heavy Industries SRK50ZSA-W air conditioners (and similar models) in Home Assistant using a Broadlink RM Pro 4.

## Features

- Control power on/off
- Set operation mode (heat, cool, dry, fan, auto)
- Set temperature
- Control fan speed with various levels:
  - quiet
  - low
  - medium
  - medium_high
  - high
  - auto
  - strong
- Control vertical swing position
- Control horizontal swing position

## Installation

### Method 1: HACS Custom Repository

1. In HACS, go to "Integrations"
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Enter the repository URL: `https://github.com/thedavidthomas/ha-mitsubishi-heavy-ac`
5. Select "Integration" as the category
6. Click "Add"
7. Install the integration from HACS

### Method 2: Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/mitsubishi_heavy_ac` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
climate:
  - platform: mitsubishi_heavy_ac
    name: Living Room AC
    host: 192.168.1.123  # Your Broadlink RM Pro IP address
    mac: 'AA:BB:CC:DD:EE:FF'  # Your Broadlink RM Pro MAC address
    min_temp: 17  # Optional, defaults to 17
    max_temp: 30  # Optional, defaults to 30
```

## Usage

After installation and configuration, the climate entity will be available in your Home Assistant. You can control:

- **Operation mode**: Off, Auto, Cool, Dry, Fan, Heat
- **Temperature**: Between min_temp and max_temp (default 17-30°C)
- **Fan speed**: Auto, Quiet, Low, Medium, Medium High, High, Strong
- **Swing mode**: Multiple options for both vertical and horizontal airflow direction

## Troubleshooting

- Make sure your Broadlink RM Pro is already set up and working in Home Assistant
- Ensure the Broadlink device has line-of-sight to the air conditioner
- Check Home Assistant logs for error messages

## Credits

Based on the arduino-heatpumpir library by ToniA: https://github.com/ToniA/arduino-heatpumpir