#!/usr/bin/env python3
"""
Generate YAML module file from checklist JSON file.

Usage:
    python3 generate_module.py <category_name> [--update]
    
Example:
    python3 generate_module.py center_panel
    python3 generate_module.py radio_panel --update
    
This will read checklist/<category_name>.json and generate/update 
definitions/modules/TFDI_MD11_<category_name>.yaml

With --update flag, it will update an existing YAML file instead of overwriting it.
"""

import json
import re
import sys
from pathlib import Path

def format_comment_name(event_name):
    """Extract and format a readable name for comments from event name."""
    # Remove common prefixes (handled by module prefix in header)
    name = event_name
    
    # Extract the base control name
    patterns = [
        (r'.*_BRT_KB_WHEEL', 'BRT Wheel Controls'),
        (r'.*_KB_WHEEL_(UP|DOWN)', 'Wheel Controls'),
        (r'.*_LSK_(\d+)(L|R)', lambda m: f'Line Select Key {m.group(1)}{m.group(2)}'),
        (r'.*_DIR_INTC', 'DIR'),
        (r'.*_ENG_OUT', 'ENG'),
        (r'.*_SEC_FPLN', 'SEC'),
        (r'.*_NAV_RAD', 'NAV'),
        (r'.*_PULL_BT', 'Pull Button'),
        (r'.*_PUSH_BT', 'Push Button'),
        (r'.*_GRD_LEFT_BUTTON', 'Ground Button'),
        (r'.*_SW_(LEFT|RIGHT)_BUTTON', 'Switch'),
        (r'.*_BT_LEFT_BUTTON_(DOWN|UP)', 'Button'),
    ]
    
    # Extract base name before event type
    base_match = re.match(r'[^_]+_(.+?)_(BT|SW|KB|GRD)_', event_name)
    if base_match:
        base = base_match.group(1)
        # Format the base name
        base = base.replace('_', ' ')
        return base.title()
    
    # Fallback: just use the event name
    return event_name

def load_variables():
    """Load L: variables from variables.json file."""
    variables_file = Path(__file__).parent / "variables.json"
    if not variables_file.exists():
        print(f"Warning: variables.json not found at {variables_file}", file=sys.stderr)
        return set()
    
    with open(variables_file) as f:
        data = json.load(f)
    
    variables = set(data.get('variables', []))
    print(f"Loaded {len(variables)} variables from variables.json", file=sys.stderr)
    return variables

def find_l_variable(event_name, variables):
    """
    Find corresponding L: variable for an event.
    
    Mapping patterns:
    - PED_CPT_RADIO_PNL_VHF1_BT_LEFT_BUTTON_DOWN -> MD11_PED_CPT_RADIO_PNL_VHF1_BT
    - OBS_AUDIO_PNL_VHF1_MIC_BT_LEFT_BUTTON_DOWN -> MD11_OBS_AUDIO_PNL_VHF1_MIC_BT
    - PED_CPT_AUDIO_PNL_VHF1_MIC_BT_LEFT_BUTTON_DOWN -> MD11_PED_CPT_AUDIO_PNL_VHF1_MIC_BT
    """
    # Remove event suffixes to get base control name
    # Important: Keep _BT, _SW, etc. in the base name
    base = event_name
    
    # Remove button/switch event suffixes (but keep _BT, _SW prefixes)
    patterns_to_remove = [
        r'_LEFT_BUTTON_(DOWN|UP)$',      # Remove _LEFT_BUTTON_DOWN/UP
        r'_RIGHT_BUTTON_(DOWN|UP)$',     # Remove _RIGHT_BUTTON_DOWN/UP
        r'_GRD_LEFT_BUTTON_DOWN$',       # Remove _GRD_LEFT_BUTTON_DOWN
        r'_KB_WHEEL_(UP|DOWN)$',         # Remove _KB_WHEEL_UP/DOWN
        r'_WHEEL_(UP|DOWN)$',            # Remove _WHEEL_UP/DOWN
    ]
    
    for pattern in patterns_to_remove:
        base = re.sub(pattern, '', base)
    
    # Try to find matching variable
    # Pattern: MD11_<event_base>
    var_name = f"MD11_{base}"
    if var_name in variables:
        return f"L:{var_name}"
    
    return None

def group_events(events, variables=None):
    """Group events by control, handling DOWN/UP pairs and wheel events."""
    if variables is None:
        variables = set()
    
    grouped = {}
    
    for event in events:
        event = event.strip().replace(' // present', '')
        if not event:
            continue
            
        # Extract base name
        # Handle brightness wheel events (e.g., PED_DU1_BRT_KB_WHEEL_UP)
        if '_BRT_KB_WHEEL_' in event:
            # Extract base like: PED_DU1_BRT_KB (keep full prefix including _BRT_KB)
            base_match = re.match(r'(.+?_BRT_KB)_WHEEL_(UP|DOWN)', event)
            if base_match:
                base = base_match.group(1)
            else:
                base = event.split('_BRT_KB_WHEEL_')[0] + '_BRT_KB'
            is_wheel = True
        elif '_KB_WHEEL_' in event:
            # Match pattern like: OBS_AUDIO_PNL_ADF1_VOL_KB_WHEEL_UP
            # We want base: OBS_AUDIO_PNL_ADF1_VOL_KB (including _KB)
            base_match = re.match(r'(.+?_KB)_WHEEL_(UP|DOWN)', event)
            if base_match:
                # Keep the full base name including _KB (e.g., OBS_AUDIO_PNL_ADF1_VOL_KB)
                base = base_match.group(1)
            else:
                # Fallback: try without _KB requirement
                base_match = re.match(r'(.+?)_KB_WHEEL_(UP|DOWN)', event)
                if base_match:
                    base = base_match.group(1) + '_KB'
                else:
                    base = 'WHEEL'
            is_wheel = True
        elif '_BT_LEFT_BUTTON_DOWN' in event:
            # Keep _BT in base name to distinguish from _SW (e.g., LSIDE_TIMER_BT)
            base = event.replace('_BT_LEFT_BUTTON_DOWN', '_BT')
            is_wheel = False
        elif '_BT_LEFT_BUTTON_UP' in event:
            # Keep _BT in base name to distinguish from _SW
            base = event.replace('_BT_LEFT_BUTTON_UP', '_BT')
            is_wheel = False
        elif '_SW_LEFT_BUTTON_DOWN' in event:
            # Keep _SW in base name to distinguish from _BT (e.g., LSIDE_TIMER_SW)
            base = event.replace('_SW_LEFT_BUTTON_DOWN', '_SW')
            is_wheel = False
        elif '_SW_RIGHT_BUTTON_DOWN' in event:
            # Keep _SW in base name and add _RIGHT marker
            # For RIGHT buttons, we still group with the same control
            base = event.replace('_SW_RIGHT_BUTTON_DOWN', '_SW')
            is_wheel = False
        elif '_GRD_LEFT_BUTTON_DOWN' in event:
            # Keep _GRD in base name (e.g., CTR_SLAT_STOW_GRD)
            base = event.replace('_GRD_LEFT_BUTTON_DOWN', '_GRD')
            is_wheel = False
        else:
            # Fallback
            base = event
            is_wheel = False
        
        if base not in grouped:
            grouped[base] = {
                'DOWN': None,
                'UP': None,
                'LEFT': None,
                'RIGHT': None,
                'GRD': None,
                'events': [],
                'is_wheel': is_wheel,
                'l_variable': None,
                'control_type': None
            }
        
        grouped[base]['events'].append(event)
        
        if '_WHEEL_DOWN' in event or '_BT_LEFT_BUTTON_DOWN' in event or '_SW_LEFT_BUTTON_DOWN' in event:
            grouped[base]['DOWN'] = event
        elif '_WHEEL_UP' in event or '_BT_LEFT_BUTTON_UP' in event:
            grouped[base]['UP'] = event
        elif '_SW_RIGHT_BUTTON_DOWN' in event:
            grouped[base]['RIGHT'] = event
        elif '_GRD_LEFT_BUTTON_DOWN' in event:
            grouped[base]['GRD'] = event
    
    # Check for L: variables for each group
    for base, group in grouped.items():
        if group['is_wheel'] and group['DOWN'] and group['UP']:
            # For wheel events, construct variable name from base name
            # Base is already extracted (e.g., OBS_AUDIO_PNL_ADF1_VOL_KB)
            var_name = f"MD11_{base}"
            if var_name in variables:
                group['l_variable'] = f"L:{var_name}"
                group['control_type'] = 'NumIncrement'
        elif not group['is_wheel'] and group['DOWN'] and group['UP']:
            # For button events, check if there's a corresponding L: variable (ToggleSwitch)
            l_var = find_l_variable(group['DOWN'], variables)
            if l_var:
                group['l_variable'] = l_var
                group['control_type'] = 'ToggleSwitch'
    
    return grouped

def generate_yaml(category_name, events, description, variables=None):
    """Generate YAML content from events."""
    if variables is None:
        variables = set()
    
    grouped = group_events(events, variables)
    
    lines = []
    lines.append(f"# TFDI MD-11 {description}")
    lines.append("# Events reference: https://docs.tfdidesign.com/md11/integration-guide/events")
    lines.append("# Variables reference: https://docs.tfdidesign.com/md11/integration-guide/variables")
    lines.append("")
    lines.append("shared:")
    
    # Sort groups for consistent output
    for base in sorted(grouped.keys()):
        group = grouped[base]
        comment = format_comment_name(group['events'][0] if group['events'] else base)
        
        # Handle wheel events with L: variables (NumIncrement)
        if group['is_wheel'] and group['l_variable'] and group['DOWN'] and group['UP']:
            lines.append(f"  - # {comment}")
            lines.append(f"    type: NumIncrement")
            lines.append(f"    var_name: {group['l_variable']}")
            lines.append(f"    var_units: Number")
            lines.append(f"    var_type: f64")
            lines.append(f"    up_event_name: {group['UP']}")
            lines.append(f"    down_event_name: {group['DOWN']}")
            lines.append(f"    increment_by: 1")
            lines.append("")  # Blank line between groups
            continue
        
        # Handle wheel events without L: variables (regular events)
        if group['is_wheel']:
            lines.append(f"  - # {comment}")
            if group['DOWN']:
                lines.append(f"    type: event")
                lines.append(f"    event_name: {group['DOWN']}")
            if group['UP']:
                if group['DOWN']:
                    lines.append("  -")
                lines.append(f"    type: event")
                lines.append(f"    event_name: {group['UP']}")
            lines.append("")  # Blank line between groups
            continue
        
        # Handle button/switch events with L: variables (ToggleSwitch)
        if group['l_variable'] and group['DOWN'] and group['UP']:
            lines.append(f"  - # {comment}")
            lines.append(f"    type: ToggleSwitch")
            lines.append(f"    var_name: {group['l_variable']}")
            lines.append(f"    var_units: Bool")
            lines.append(f"    var_type: bool")
            lines.append(f"    event_name: {group['DOWN']}")
            lines.append(f"    off_event_name: {group['UP']}")
            lines.append("")  # Blank line between groups
            continue
        
        # Handle button/switch events without L: variables (regular events)
        lines.append(f"  - # {comment}")
        
        # Add DOWN event if present
        if group['DOWN']:
            lines.append(f"    type: event")
            lines.append(f"    event_name: {group['DOWN']}")
        
        # Add UP event if present
        if group['UP']:
            if group['DOWN']:
                lines.append("  -")
            lines.append(f"    type: event")
            lines.append(f"    event_name: {group['UP']}")
        
        # Add RIGHT event (for switches)
        if group['RIGHT']:
            if group['DOWN'] or group['UP']:
                lines.append("  -")
            lines.append(f"    type: event")
            lines.append(f"    event_name: {group['RIGHT']}")
        
        # Add GRD event (for ground buttons)
        if group['GRD']:
            if group['DOWN'] or group['UP'] or group['RIGHT']:
                lines.append("  -")
            lines.append(f"    type: event")
            lines.append(f"    event_name: {group['GRD']}")
        
        # If only single events without DOWN/UP pattern, list them all
        if not group['DOWN'] and not group['UP'] and not group['RIGHT'] and not group['GRD']:
            for event in group['events']:
                if group['events'].index(event) > 0:
                    lines.append("  -")
                lines.append(f"    type: event")
                lines.append(f"    event_name: {event}")
        
        lines.append("")  # Blank line between groups
    
    return "\n".join(lines) + "\n"

def update_existing_yaml(output_file, events, description, variables):
    """Update existing YAML file with new events, preserving structure."""
    if not output_file.exists():
        print(f"Error: File not found: {output_file}", file=sys.stderr)
        print("Use without --update flag to create a new file.", file=sys.stderr)
        sys.exit(1)
    
    # Read existing file
    with open(output_file) as f:
        existing_content = f.read()
    
    # Extract existing event names
    existing_events = set(re.findall(r'event_name:\s*([A-Z0-9_]+)', existing_content))
    
    # Find new events
    new_events = [e for e in events if e not in existing_events]
    
    if not new_events:
        print(f"No new events to add. All {len(events)} events already present.")
        return
    
    print(f"Found {len(new_events)} new events to add")
    
    # For now, just regenerate the whole file
    # TODO: Could be smarter and insert new events in appropriate places
    yaml_content = generate_yaml(None, events, description, variables)
    
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"Updated: {output_file}")
    print(f"Total events: {len(events)}")

def clean_checklist_file(checklist_file):
    """Remove '// present' comments from checklist JSON file."""
    with open(checklist_file) as f:
        data = json.load(f)
    
    # Remove " // present" from all events
    events = data.get('events', [])
    cleaned_events = [e.strip().replace(' // present', '') for e in events if e.strip()]
    data['events'] = cleaned_events
    data['present_count'] = 0
    
    # Write back to file
    with open(checklist_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    
    return len(cleaned_events)

def update_checklist_file(checklist_file, events):
    """Update checklist JSON file to mark all events as '// present' (inside string value, like check_events.py)."""
    with open(checklist_file) as f:
        data = json.load(f)
    
    # Mark all events as present (with " // present" inside the string value)
    data['events'] = [f"{event} // present" for event in events]
    data['present_count'] = len(events)
    
    # Write back to file using json.dump (same format as check_events.py)
    with open(checklist_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add trailing newline
    
    print(f"Updated checklist: {checklist_file.name} ({len(events)}/{len(events)} events marked as present)")

def regenerate_all_modules():
    """Regenerate all TFDI MD-11 modules from scratch."""
    checklist_dir = Path(__file__).parent
    modules_dir = checklist_dir.parent / "definitions" / "modules"
    
    print("=" * 60)
    print("REGENERATING ALL TFDI MD-11 MODULES")
    print("=" * 60)
    
    # Step 1: Delete all TFDI_MD11_*.yaml files
    print("\nStep 1: Deleting existing TFDI_MD11_*.yaml files...")
    deleted_count = 0
    if modules_dir.exists():
        for module_file in modules_dir.glob("TFDI_MD11_*.yaml"):
            module_file.unlink()
            deleted_count += 1
            print(f"  Deleted: {module_file.name}")
    print(f"Deleted {deleted_count} module files")
    
    # Step 2: Clean all JSON checklist files (remove // present comments)
    print("\nStep 2: Cleaning JSON checklist files (removing // present comments)...")
    checklist_files = sorted(checklist_dir.glob("*.json"))
    # Exclude variables.json
    checklist_files = [f for f in checklist_files if f.name != "variables.json"]
    
    cleaned_count = 0
    for checklist_file in checklist_files:
        event_count = clean_checklist_file(checklist_file)
        cleaned_count += 1
        print(f"  Cleaned: {checklist_file.name} ({event_count} events)")
    print(f"Cleaned {cleaned_count} checklist files")
    
    # Step 3: Generate all modules
    print("\nStep 3: Generating all modules...")
    variables = load_variables()
    
    generated_count = 0
    for checklist_file in checklist_files:
        category = checklist_file.stem
        output_file = modules_dir / f"TFDI_MD11_{category}.yaml"
        
        try:
            # Read checklist
            with open(checklist_file) as f:
                data = json.load(f)
            
            events = data.get('events', [])
            description = data.get('description', category.replace('_', ' ').title())
            
            # Strip any remaining "// present" markers
            events = [e.strip().replace(' // present', '') for e in events if e.strip()]
            
            if not events:
                print(f"  Skipping {category} (no events)")
                continue
            
            # Generate YAML
            yaml_content = generate_yaml(category, events, description, variables)
            
            # Write output
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(yaml_content)
            
            toggle_count = yaml_content.count('type: ToggleSwitch')
            num_increment_count = yaml_content.count('type: NumIncrement')
            
            print(f"  Generated: {category} ({len(events)} events, {toggle_count} ToggleSwitches, {num_increment_count} NumIncrements)")
            
            # Update checklist file to mark events as present
            update_checklist_file(checklist_file, events)
            
            generated_count += 1
        except Exception as e:
            print(f"  ERROR generating {category}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nGenerated {generated_count} modules")
    
    # Step 4: Run check_events on all categories
    print("\nStep 4: Running check_events on all categories...")
    print("-" * 60)
    
    # Import check_events module
    import importlib.util
    check_events_path = checklist_dir / "check_events.py"
    spec = importlib.util.spec_from_file_location("check_events", check_events_path)
    check_events_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_events_module)
    
    total_present = 0
    total_events = 0
    
    for checklist_file in checklist_files:
        try:
            present, total = check_events_module.check_events_for_category(checklist_file)
            total_present += present
            total_events += total
        except Exception as e:
            print(f"ERROR checking {checklist_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"FINAL SUMMARY: {total_present}/{total_events} events are present in YAML files")
    if total_events > 0:
        print(f"Coverage: {total_present/total_events*100:.1f}%")
    print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_module.py <category_name> [--update]", file=sys.stderr)
        print("       python3 generate_module.py --regenerate-all", file=sys.stderr)
        sys.exit(1)
    
    # Check for --regenerate-all flag
    if '--regenerate-all' in sys.argv:
        regenerate_all_modules()
        return
    
    category = sys.argv[1]
    update_mode = '--update' in sys.argv
    
    checklist_file = Path(__file__).parent / f"{category}.json"
    output_file = Path(__file__).parent.parent / "definitions" / "modules" / f"TFDI_MD11_{category}.yaml"
    
    if not checklist_file.exists():
        print(f"Error: Checklist file not found: {checklist_file}", file=sys.stderr)
        sys.exit(1)
    
    # Load variables
    variables = load_variables()
    
    # Read checklist
    with open(checklist_file) as f:
        data = json.load(f)
    
    events = data.get('events', [])
    description = data.get('description', category.replace('_', ' ').title())
    
    # Strip "// present" markers (added by check_events.py or generate_module.py)
    events = [e.strip().replace(' // present', '') for e in events if e.strip()]
    
    if update_mode:
        update_existing_yaml(output_file, events, description, variables)
    else:
        # Generate YAML
        yaml_content = generate_yaml(category, events, description, variables)
        
        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(yaml_content)
        
        print(f"Generated: {output_file}")
        print(f"Events: {len(events)}")
        
        # Count control types
        toggle_count = yaml_content.count('type: ToggleSwitch')
        num_increment_count = yaml_content.count('type: NumIncrement')
        if toggle_count > 0:
            print(f"ToggleSwitches: {toggle_count}")
        if num_increment_count > 0:
            print(f"NumIncrements: {num_increment_count}")
    
    # Update checklist file to mark all events as present
    update_checklist_file(checklist_file, events)

if __name__ == '__main__':
    main()

