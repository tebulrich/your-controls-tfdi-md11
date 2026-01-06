# TFDi Design MD-11 YourControls Configuration

YourControls configuration files for the TFDi Design MD-11 aircraft. This project provides complete event coverage for all aircraft systems and panels.

## Table of Contents

- [Overview](#overview)
- [Status](#status)
- [Documentation References](#documentation-references)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Category System](#category-system)
- [Module Generator](#module-generator)
- [Event Type Patterns](#event-type-patterns)
- [Workflow](#workflow)
- [File Locations](#file-locations)

## Overview

This project creates comprehensive YourControls configuration files for the TFDi Design MD-11 aircraft. The configuration is organized into modular YAML files, with each module covering a specific panel/system. All events are consolidated into a single main aircraft configuration file.

## Status

1423 events across 19 categories have been implemented and verified.

### Completed Modules

1. Audio Panel - Audio panel controls (Captain, First Officer, Observer)
2. Radio Panel - Radio panel controls
3. FMC/CDU - FMC/CDU button events (LMCDU, RMCDU, CDU, CMCDU)
4. Aft Overhead Panel - Aft overhead panel (APU, Fire, Cargo Smoke, GPWS, Evacuation)
5. Overhead Panel - Main overhead panel
6. Center Glareshield - Center glareshield / Autopilot Control Panel
7. Glareshield Left - Left glareshield
8. Glareshield Right - Right glareshield
9. Center Panel - Center panel
10. Pedestal - Pedestal controls
11. Left Side Panel - Left side panel
12. Right Side Panel - Right side panel
13. Left ECP - Left ECP
14. Right ECP - Right ECP
15. Left Yoke - Left yoke controls
16. Right Yoke - Right yoke controls
17. Flight Controls - Flight controls
18. Throttle - Throttle controls
19. Main Instruments Panel - Main instruments panel

All events are consolidated in: `definitions/aircraft/TFDi Design - MD-11.yaml`

## Documentation References

- [Events Documentation](https://docs.tfdidesign.com/md11/integration-guide/events)
- [Variables Documentation](https://docs.tfdidesign.com/md11/integration-guide/variables)

## Project Structure

```
your-controls-tfdi-md11/
├── definitions/
│   ├── aircraft/
│   │   └── TFDi Design - MD-11.yaml    # Main aircraft configuration
│   └── modules/
│       ├── tfdi-md11/                   # TFDi MD-11 modules (when not merged)
│       └── *.yaml                       # Standard YourControls modules
├── tfdi-md11-data/
│   ├── *.json                          # Category definition files
│   └── variables.json                  # L: variable definitions
├── generate.py                          # Module generator script
├── validate.py                          # Coverage verification script
└── README.md                           # This file
```

## Quick Start

### Verify Coverage

Check coverage for a specific category:
```bash
python3 validate.py <category_name>
```

Check all categories:
```bash
python3 validate.py
```

### Regenerate Configuration

Regenerate all categories and merge into main file:
```bash
python3 generate.py
```

## Category System

The `tfdi-md11-data/` folder contains JSON files for each panel/system category. Each JSON file lists all events from the documentation that should be implemented for that category.

The `validate.py` script:
- Searches for each event in the main aircraft YAML file
- Marks events as "// present" in the JSON file if found
- Reports coverage percentage

## Module Generator

A Python script (`generate.py`) automatically generates YAML module files from category JSON files.

### Usage

```bash
# Regenerate all categories (merges into main aircraft file by default)
python3 generate.py

# Generate a single category (merges into main aircraft file)
python3 generate.py <category_name>

# Regenerate all categories as separate module files
python3 generate.py --split

# Generate a single category as separate module file
python3 generate.py <category_name> --split

# Specify custom output path for aircraft file
python3 generate.py --output-path E:\YourControls\definitions\aircraft
python3 generate.py --output-path E:\YourControls\definitions\aircraft\
python3 generate.py <category_name> --output-path E:\YourControls\definitions\aircraft
```

### What It Does

1. Reads the category JSON file (`tfdi-md11-data/<category_name>.json`)
2. Extracts all events (automatically filters out "// present" markers)
3. Groups events by control type (buttons, wheels, switches, etc.)
4. Detects L: variables from `tfdi-md11-data/variables.json` to determine control types
5. Generates properly formatted YAML with appropriate types (event, ToggleSwitch, NumIncrement)
6. Marks all implemented events as "// present" in the JSON category file

### Features

- Handles button DOWN/UP pairs automatically
- Groups wheel events (WHEEL_UP/WHEEL_DOWN)
- Handles switches with LEFT/RIGHT buttons
- Handles ground buttons (GRD_LEFT_BUTTON_DOWN)
- Automatically detects ToggleSwitch types for controls with Bool L: variables
- Automatically detects NumIncrement types for wheel controls with numeric L: variables
- Generates appropriate comments for each control group
- Creates standard headers with references to documentation
- Supports property overrides via object format in JSON files

### Event Overrides

The generator supports overriding YAML properties for individual events. While the default format uses simple strings:

```json
"events": [
  "CTR_ANTISKID_BT_LEFT_BUTTON_DOWN",
  "CTR_ANTISKID_BT_LEFT_BUTTON_UP"
]
```

You can use an object format to specify overrides:

```json
"events": [
  "CTR_ANTISKID_BT_LEFT_BUTTON_DOWN",
  {
    "event": "CTR_AUX_HYD_PUMP_BT_LEFT_BUTTON_DOWN",
    "unreliable": true,
    "use_calculator": true
  }
]
```

**Supported Override Properties:**
- `type` - Override the control type (e.g., `"NumSet"`, `"ToggleSwitch"`, `"event"`)
- `unreliable` - Mark the event as unreliable (boolean)
- `use_calculator` - Enable calculator for value transformations (boolean)
- `add_by` - Add an offset value (number)
- `multiply_by` - Multiply by a factor (number)
- `increment_by` - Override increment step size (number, for NumIncrement)
- `cancel_h_events` - Cancel H events (boolean)
- Any other YAML property supported by YourControls

The generator will automatically apply these overrides to the generated YAML entries. Both formats can be mixed in the same JSON file - the generator maintains backward compatibility with the string format.

### Flags

- `--split`: Creates separate module files in `definitions/modules/tfdi-md11/` instead of merging into the main aircraft file. The aircraft file will include references to these modules. Works with both all categories and single category. By default (without `--split`), all events are merged directly into the main aircraft YAML file.

- `--output-path` or `--output`: Specifies a custom directory path for the output aircraft YAML file. The path can include or omit a trailing slash. The output file will be named `TFDi Design - MD-11.yaml` in the specified directory. If the directory doesn't exist, it will be created automatically. This overrides the path specified in `config.json`.

### Configuration File

You can create a `config.json` file in the project root to set default values:

```json
{
  "output_path": "E:\\YourControls\\definitions\\aircraft"
}
```

The `output_path` setting will be used automatically if no `--output-path` argument is provided. Command-line arguments always override the config file.

### Behavior

- Running without arguments (`python3 generate.py`): Regenerates all categories and merges into main aircraft file
- Running with a category name (`python3 generate.py center_panel`): Regenerates only that category and merges into main aircraft file
- Running with `--split` flag (`python3 generate.py --split`): Regenerates all categories as separate module files
- Running with category and `--split` (`python3 generate.py center_panel --split`): Generates that category as a separate module file

### Deduplication

The generator automatically prevents duplicate entries when merging categories:

- **All categories mode**: Preserves manually-added entries (those without `L:MD11_` variables or generated event patterns) and replaces all generated entries with fresh content from categories
- **Single category mode**: Preserves manually-added entries and entries from other categories, but replaces entries from the category being regenerated to prevent duplicates
- Generated entries are identified by the presence of `L:MD11_` variables or event patterns like `_BT_LEFT_BUTTON`, `_KB_WHEEL`, `_SW_LEFT_BUTTON`, or `_GRD_LEFT_BUTTON`

This ensures that running the generator multiple times does not create duplicate entries in the output file.

## Event Type Patterns

### ToggleSwitch

For controls with on/off state that have L: variables:

```yaml
type: ToggleSwitch
var_name: L:MD11_VARIABLE_NAME
var_units: Bool
var_type: bool
event_name: EVENT_DOWN
off_event_name: EVENT_UP
```

### Event

For momentary button presses, wheel events, switches without state tracking:

```yaml
type: event
event_name: EVENT_NAME
```

### NumIncrement

For controls that increment/decrement values:

```yaml
type: NumIncrement
var_name: L:MD11_VARIABLE_NAME
var_units: Number
var_type: f64
up_event_name: EVENT_WHEEL_UP
down_event_name: EVENT_WHEEL_DOWN
increment_by: 1
```

## Workflow

### Regenerating the Configuration

To regenerate the entire configuration from scratch:

```bash
# Regenerate all categories and merge into main aircraft file
python3 generate.py

# Verify coverage
python3 validate.py
```

### Updating a Single Category

To regenerate a specific category:

```bash
# Regenerate a single category
python3 generate.py <category_name>

# Verify coverage for that category
python3 validate.py <category_name>
```

### Working with Separate Module Files

If you prefer to work with separate module files instead of a merged configuration:

```bash
# Generate all categories as separate module files
python3 generate.py --split

# Generate a single category as a separate module file
python3 generate.py <category_name> --split
```

The generator script automatically:
- Groups related events together
- Detects appropriate control types (ToggleSwitch, NumIncrement, event)
- Formats YAML with proper indentation and comments
- Updates category files to mark events as present

### Verification

After generating or modifying the configuration, always verify coverage:

```bash
# Check all categories
python3 validate.py

# Check a specific category
python3 validate.py <category_name>
```

## Important Notes

1. Event prefixes follow specific patterns: Observer events use `OBS_` prefix, Captain/First Officer events use `PED_CPT_` and `PED_FO_` prefixes
2. Some controls have both button events (`_BT_LEFT_BUTTON_DOWN/UP`) and wheel events (`_KB_WHEEL_UP/DOWN`)
3. Not all events have corresponding L: variables - the generator automatically uses `type: event` when no variable exists
4. The `validate.py` script marks events as "// present" in JSON files - this is expected behavior and helps track coverage
5. YAML syntax requires strict indentation (2 spaces) - the generator handles this automatically

## File Locations

- Main aircraft config: `definitions/aircraft/TFDi Design - MD-11.yaml`
- Module files (non-merged): `definitions/modules/tfdi-md11/TFDi_MD11_*.yaml`
- Category files: `tfdi-md11-data/*.json`
- Variables file: `tfdi-md11-data/variables.json`
- Validation script: `validate.py`
- Generator script: `generate.py`

## Grouping Logic

The grouping logic in `generate.py` has been carefully refined to handle all event patterns:

1. **Control Type Distinction**: Buttons (_BT) and switches (_SW) are grouped separately even if they share the same base name
2. **Brightness Wheel Events**: _BRT_KB_WHEEL events extract the full prefix (e.g., PED_DU1_BRT_KB)
3. **Ground Button Events**: _GRD_LEFT_BUTTON_DOWN events are preserved as separate controls with _GRD suffix
4. **Switch RIGHT Buttons**: _SW_RIGHT_BUTTON_DOWN events are grouped with their corresponding _SW_LEFT_BUTTON_DOWN control
5. **L: Variable Detection**: The script loads variables from `tfdi-md11-data/variables.json` (1477 variables) and automatically detects ToggleSwitch and NumIncrement types

These fixes ensure that all events are correctly grouped, generated, and detected, achieving 100% coverage (1423/1423 events across all categories).

