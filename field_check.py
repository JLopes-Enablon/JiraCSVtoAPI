import json
import os
from pathlib import Path

def load_jira_fields(json_path='jira_fields.json'):
    if not Path(json_path).is_file():
        print(f"Jira field metadata file '{json_path}' not found.")
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_field_map(fields_json):
    """Return a dict mapping field names to their IDs and schema."""
    return {f['name']: f for f in fields_json}

def prompt_field_mapping(field_map, current_fields):
    """
    Prompt the user to review and optionally update custom field mappings.
    current_fields: dict of {system_field: custom_field_id}
    Returns: dict of {system_field: custom_field_id}
    """
    print("\n--- Jira Field Mapping Review ---")
    new_fields = {}
    for sys_field, custom_id in current_fields.items():
        print(f"System field: {sys_field}")
        print(f"Current Jira field: {custom_id}")
        # Show available fields with similar names
        matches = [fid for fname, fid in field_map.items() if sys_field.lower() in fname.lower()]
        if matches:
            print("Possible matches:")
            for m in matches:
                print(f"  - {m['name']} ({m['id']})")
        choice = input(f"Press Enter to keep '{custom_id}', or type a new field ID: ").strip()
        if choice:
            new_fields[sys_field] = choice
        else:
            new_fields[sys_field] = custom_id
    print("Field mapping complete.\n")
    return new_fields

def is_field_on_screen(field_id, issue_type, fields_json):
    """
    Check if a field is available for a given issue type.
    This is a best-effort check; Jira's REST API does not always expose screen info.
    """
    # This function can be expanded if you have more metadata
    for f in fields_json:
        if f['id'] == field_id:
            # If 'schema' or 'scope' info is present, you can add more checks here
            return True
    return False

if __name__ == "__main__":
    import sys
    fields_json = load_jira_fields()
    field_map = get_field_map(fields_json)
    # Example: current field mapping
    current_fields = {
        'Story Points': 'customfield_10037',
        'Actual Start': 'customfield_10008',
    }
    new_fields = prompt_field_mapping(field_map, current_fields)
    # If a file path is provided as an argument, write the mapping to that file
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            json.dump(new_fields, f)
    print("Final field mapping:", new_fields)
