# Mitsubishi Heavy Industries AC - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Control your Mitsubishi Heavy Industries air conditioning units with Home Assistant through a Broadlink RM Pro device.

## Overview

This integration allows you to control your Mitsubishi Heavy Industries air conditioner through Home Assistant using a Broadlink RM Pro IR blaster. It provides most of the functionality available on your physical remote control.

## Features

- **Power**: On/Off control
- **Mode**: Heat, Cool, Dry, Fan, Auto
- **Temperature**: Set temperature
- **Fan Speed**: Quiet, Low, Medium, Medium_High, High, Auto, Strong
- **Swing**: Vertical and horizontal swing control
- **Display**: Display light control

## Installation

### Option 1: HACS (recommended)

1. Ensure that [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL `https://github.com/thedavidthomas/ha-mitsubishi-heavy-ac`
   - Select "Integration" as the category
3. Click "Install"
4. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release
2. Copy the `custom_components/mitsubishi_heavy_ac` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Option 1: Using a Broadlink Remote Entity (Recommended)

If you already have a Broadlink RM Pro configured in Home Assistant:

```yaml
climate:
  - platform: mitsubishi_heavy_ac
    name: Living Room AC
    remote_entity_id: remote.rm4_pro_remote
```

### Option 2: Direct IP/MAC Configuration

```yaml
climate:
  - platform: mitsubishi_heavy_ac
    name: Living Room AC
    host: 192.168.1.123 # Your Broadlink RM Pro IP address
    mac: "AA:BB:CC:DD:EE:FF" # Your Broadlink RM Pro MAC address
```

### Configuration Options

| Option           | Type   | Required | Default | Description                               |
| ---------------- | ------ | -------- | ------- | ----------------------------------------- |
| name             | string | Yes      | -       | Name of the climate entity                |
| remote_entity_id | string | No\*     | -       | Entity ID of your Broadlink RM Pro remote |
| host             | string | No\*     | -       | IP address of your Broadlink RM Pro       |
| mac              | string | No\*     | -       | MAC address of your Broadlink RM Pro      |
| temperature_unit | string | No       | C       | Temperature unit (C or F)                 |
| min_temp         | number | No       | 16      | Minimum temperature setting               |
| max_temp         | number | No       | 30      | Maximum temperature setting               |

\* Either `remote_entity_id` OR both `host` and `mac` must be provided.

## Troubleshooting

### AC Not Responding

- Ensure your Broadlink RM Pro has line-of-sight to the AC unit
- Verify the IP address is correct and static
- Check that your Broadlink device is on the same network as Home Assistant

### Commands Not Working Correctly

- Some AC models have slight variations in their IR protocols
- Try learning the specific commands from your remote

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Development

### Validating the Component

To check for common errors in the component:

```bash
python validate_component.py
```

This will check for:

- Syntax errors in Python files
- Proper manifest.json configuration
- Deprecated Home Assistant imports
- Translation files structure

### Manual Testing

1. Install the component in a development Home Assistant instance
2. Enable debug logging for the component
3. Check the logs for any errors or warnings
