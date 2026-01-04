#!/usr/bin/env python3
"""
Check which events from checklist JSON files are already present in YAML definition files.
Updates the JSON files by appending " // present" to event names that are found.
"""

import json
import os
import re
from pathlib import Path

# Paths
CHECKLIST_DIR = Path(__file__).parent
AIRCRAFT_FILE = CHECKLIST_DIR.parent / "definitions" / "aircraft" / "TFDi Design - MD-11.yaml"
MODULES_DIR = CHECKLIST_DIR.parent / "definitions" / "modules"

def load_yaml_file(filepath):
    """Load YAML file content as text for searching."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def find_event_in_yaml(event_name, yaml_content):
    """Check if event name appears in YAML content."""
    if yaml_content is None:
        return False
    
    # Escape special regex characters in event name
    escaped_event = re.escape(event_name)
    
    # Look for event_name: EVENT_NAME (with proper YAML spacing)
    # Pattern: event_name: EVENT_NAME (at start of value, possibly with spaces)
    patterns = [
        rf'event_name:\s+{escaped_event}\b',  # event_name: EVENT_NAME
        rf'off_event_name:\s+{escaped_event}\b',  # off_event_name: EVENT_NAME
        rf'up_event_name:\s+{escaped_event}\b',  # up_event_name: EVENT_NAME
        rf'down_event_name:\s+{escaped_event}\b',  # down_event_name: EVENT_NAME
    ]
    
    for pattern in patterns:
        if re.search(pattern, yaml_content):
            return True
    
    return False

def get_module_filename(category_name):
    """Determine the module filename based on category name."""
    # Convert category name to module filename pattern
    # e.g., "audio_panel" -> "TFDI_MD11_audio_panel.yaml"
    # e.g., "aft_overhead_panel" -> "TFDI_MD11_aft_overhead_panel.yaml"
    module_name = f"TFDI_MD11_{category_name}.yaml"
    return MODULES_DIR / module_name

def check_events_for_category(category_file):
    """Check events for a specific category and update the JSON file."""
    print(f"\nChecking {category_file.name}...")
    
    # Load checklist JSON
    with open(category_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    category = data['category']
    events = data.get('events', [])
    
    # Remove any existing " // present" comments from event names
    events = [e.split(' // present')[0] for e in events]
    
    # Load YAML files to check
    aircraft_yaml = load_yaml_file(AIRCRAFT_FILE)
    module_yaml = load_yaml_file(get_module_filename(category))
    
    # Also check other module files that might contain events
    all_module_files = []
    if MODULES_DIR.exists():
        for module_file in MODULES_DIR.glob("TFDI_MD11_*.yaml"):
            if module_file.name != get_module_filename(category).name:
                all_module_files.append((module_file.name, load_yaml_file(module_file)))
    
    # Check each event
    present_count = 0
    updated_events = []
    
    for event in events:
        found = False
        found_in = []
        
        # Check main aircraft file
        if find_event_in_yaml(event, aircraft_yaml):
            found = True
            found_in.append("main")
        
        # Check corresponding module file
        if find_event_in_yaml(event, module_yaml):
            found = True
            found_in.append("module")
        
        # Check other module files
        for module_name, module_content in all_module_files:
            if find_event_in_yaml(event, module_content):
                found = True
                found_in.append(f"module:{module_name}")
        
        # Append " // present" if found
        if found:
            present_count += 1
            updated_events.append(f"{event} // present")
            print(f"  [FOUND] {event} (in: {', '.join(found_in)})")
        else:
            updated_events.append(event)
    
    # Update the events list
    data['events'] = updated_events
    data['event_count'] = len(updated_events)
    
    # Remove the events_with_status if it exists (from previous runs)
    if 'events_with_status' in data:
        del data['events_with_status']
    if 'present_events' in data:
        del data['present_events']
    if 'present_count' in data and data['present_count'] != present_count:
        # Only update if it changed, but we'll remove it for cleaner output
        pass
    
    # Save updated JSON
    with open(category_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  Results: {present_count}/{len(events)} events present")
    return present_count, len(events)

def main():
    """Main function to check all checklist files."""
    import sys
    
    # Parse command line arguments
    target_file = None
    if len(sys.argv) > 1:
        target_arg = sys.argv[1].lower()
        # Handle various input formats: "fmc_cdu", "fmc_cdu.json", "fmc", etc.
        if "fmc" in target_arg or "cdu" in target_arg:
            target_file = "fmc_cdu.json"
        elif target_arg.endswith(".json"):
            target_file = target_arg
        else:
            # Try to find matching file
            possible_files = list(CHECKLIST_DIR.glob(f"{target_arg}*.json"))
            if possible_files:
                target_file = possible_files[0].name
            else:
                print(f"ERROR: No checklist file found matching '{target_arg}'")
                print(f"Available files: {', '.join([f.name for f in CHECKLIST_DIR.glob('*.json')])}")
                return
    
    print("Checking events in checklist files...")
    print(f"Aircraft file: {AIRCRAFT_FILE}")
    print(f"Modules directory: {MODULES_DIR}")
    
    if not AIRCRAFT_FILE.exists():
        print(f"ERROR: Aircraft file not found: {AIRCRAFT_FILE}")
        return
    
    if not MODULES_DIR.exists():
        print(f"WARNING: Modules directory not found: {MODULES_DIR}")
    
    # Get JSON files to process
    if target_file:
        checklist_file_path = CHECKLIST_DIR / target_file
        if not checklist_file_path.exists():
            print(f"ERROR: Checklist file not found: {target_file}")
            return
        checklist_files = [checklist_file_path]
        print(f"\nScanning only: {target_file}")
    else:
        # Get all JSON files in checklist directory
        checklist_files = sorted(CHECKLIST_DIR.glob("*.json"))
        print(f"\nScanning all checklist files...")
    
    if not checklist_files:
        print("No checklist files found!")
        return
    
    total_present = 0
    total_events = 0
    
    for checklist_file in checklist_files:
        try:
            present, total = check_events_for_category(checklist_file)
            total_present += present
            total_events += total
        except Exception as e:
            print(f"ERROR processing {checklist_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Summary: {total_present}/{total_events} events are present in YAML files")
    if total_events > 0:
        print(f"Coverage: {total_present/total_events*100:.1f}%")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
