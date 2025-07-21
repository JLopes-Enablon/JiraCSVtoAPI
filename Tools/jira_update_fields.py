"""
jira_update_fields.py

Update missing custom fields (e.g., Story Points, Original Estimate) for existing Jira issues listed in a CSV/output file.

Usage:
    python jira_update_fields.py [input_csv]

"""
"""
jira_update_fields.py

Bulk updates Jira issues from merged CSV, handling all field types robustly and safely.
Usage: Run directly to update Jira after review of merged.csv.
"""
import sys
import os
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from dotenv import load_dotenv
import csv
import logging
from jiraapi import JiraAPI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def update_issue_fields(jira, issue_key, story_points, original_estimate, field_mapping, **kwargs):
    errors = []
    try:
        current = jira.get_issue(issue_key)
        current_fields = current.get("fields", {})
    except Exception as e:
        logging.error(f"Failed to fetch current issue {issue_key}: {e}")
        return [str(e)]

    update_fields = {}
    # Dynamically map all CSV fields except Time Spent
    editmeta_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/editmeta"
    editmeta_response = jira.session.get(editmeta_url)
    editable_fields = {}
    if editmeta_response.ok:
        editable_fields = editmeta_response.json().get('fields', {})
        print(f"/editmeta fields for {issue_key}: {list(editable_fields.keys())}")
    else:
        print(f"Failed to fetch /editmeta for {issue_key}: {editmeta_response.status_code} {editmeta_response.text}")

    for csv_field, csv_value in kwargs.items():
        if csv_field.lower() == "time_spent" or csv_field.lower() == "time spent":
            continue  # Skip Time Spent
        # Map CSV field to Jira field using field_mapping if available
        jira_field = field_mapping.get(csv_field, csv_field.replace(" ", "_")) if field_mapping else csv_field.replace(" ", "_")
        # Special handling for common fields
        if csv_field.lower() == "priority":
            jira_val = current_fields.get("priority", {}).get("name")
            if csv_value and csv_value != jira_val and "priority" in editable_fields:
                update_fields["priority"] = {"name": csv_value}
                print(f"Will update Priority for {issue_key} to {csv_value}")
        elif csv_field.lower() == "parent":
            # Always use object format for parent
            if csv_value and "parent" in editable_fields:
                update_fields["parent"] = {"key": csv_value}
                print(f"Will update parent for {issue_key} to {{'key': '{csv_value}'}}")
        elif csv_field.lower() == "issuetype":
            # Skip updating issuetype entirely per user request
            print(f"Skipping update of issuetype for {issue_key} as requested.")
            continue
        elif csv_field.lower() == "components":
            # Components must be a list of objects with 'name'
            if csv_value and "components" in editable_fields:
                comps = [c.strip() for c in str(csv_value).split(",") if c.strip()]
                update_fields["components"] = [{"name": c} for c in comps]
                print(f"Will update components for {issue_key} to {update_fields['components']}")
        elif csv_field.lower() == "labels":
            # Labels must be a list of strings
            if csv_value and "labels" in editable_fields:
                labels = [l.strip() for l in str(csv_value).split(",") if l.strip()]
                update_fields["labels"] = labels
                print(f"Will update labels for {issue_key} to {labels}")
        elif csv_field.lower() == "story points":
            sp_fields_to_try = [field_mapping.get('Story Points', 'customfield_10146'), 'customfield_10016', 'customfield_10146']
            for sp_field in sp_fields_to_try:
                # Only update if value is a valid float and not None/empty
                if sp_field in editable_fields and csv_value and str(csv_value).strip().lower() not in ["none", ""]:
                    try:
                        update_fields[sp_field] = float(csv_value)
                        print(f"Forcing update: Story Points field {sp_field} for {issue_key}. Jira value: {current_fields.get(sp_field)}, CSV value: {csv_value}")
                    except ValueError:
                        print(f"Skipping Story Points for {issue_key}: invalid value '{csv_value}'")
                    break
                else:
                    print(f"Story Points field {sp_field} not editable or value is None/empty for {issue_key}")
        elif csv_field.lower() == "original estimate":
            oe_fields_to_try = ["timetracking", "timeoriginalestimate"]
            for oe_field in oe_fields_to_try:
                if oe_field in editable_fields and csv_value and str(csv_value).strip() != "":
                    print(f"Forcing update: Original Estimate field {oe_field} for {issue_key}. Jira value: {current_fields.get(oe_field)}, CSV value: {csv_value}")
                    if oe_field == "timetracking":
                        update_fields[oe_field] = {"originalEstimate": str(csv_value).strip()}
                    else:
                        update_fields[oe_field] = str(csv_value).strip()
                    break
                else:
                    print(f"Original Estimate field {oe_field} not editable for {issue_key}")
        else:
            jira_val = current_fields.get(jira_field)
            if jira_field in editable_fields and csv_value and str(csv_value) != str(jira_val):
                update_fields[jira_field] = csv_value
                print(f"Will update {jira_field} for {issue_key} to {csv_value}")
            else:
                print(f"Field {jira_field} not editable or value matches for {issue_key}")
    # Do NOT update Time Spent (worklog) as requested
    # time_spent = kwargs.get("Time_spent")
    # if time_spent:
    #     # Always log work, cannot compare
    #     try:
    #         jira.log_work(issue_key, time_spent)
    #         print(f"Logged work for {issue_key}: {time_spent}")
    #     except Exception as e:
    #         logging.error(f"Failed to log work for {issue_key}: {e}")
    #         errors.append(str(e))
    print(f"\n--- Debug for {issue_key} ---")
    for csv_field, csv_value in kwargs.items():
        if csv_field.lower() == "time_spent" or csv_field.lower() == "time spent":
            continue
        jira_field = field_mapping.get(csv_field, csv_field.replace(" ", "_")) if field_mapping else csv_field.replace(" ", "_")
        jira_val = current_fields.get(jira_field)
        if csv_field.lower() == "priority":
            jira_val = current_fields.get("priority", {}).get("name")
        elif csv_field.lower() == "original estimate":
            jira_val = current_fields.get("timetracking", {}).get("originalEstimate")
        print(f"Field: {csv_field} | CSV: {csv_value} | Jira: {jira_val}")
    if update_fields:
        print(f"Attempting update for {issue_key}: {update_fields}")
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
        payload = {"fields": update_fields}
        print(f"Payload: {payload}")
        try:
            response = jira.session.put(url, json=payload)
            print(f"Jira API response: {response.status_code}")
            if not response.ok:
                print(f"Response body: {response.text}")
                logging.error(f"Failed to update {issue_key}: {response.status_code} {response.text}")
                errors.append(f"{response.status_code} {response.text}")
            else:
                print(f"Updated {issue_key}: {list(update_fields.keys())}")
        except Exception as e:
            logging.error(f"Failed to update {issue_key}: {e}")
            errors.append(str(e))
    else:
        print(f"No update needed for {issue_key}. All CSV values matched Jira.")
    return errors

def main():
    # Load environment variables from .env file
    load_dotenv()
    import sys
    logging.basicConfig(filename="error.log", level=logging.ERROR)
    if len(sys.argv) < 2:
        print("Usage: python jira_update_fields.py [input_csv]")
        return
    csv_path = sys.argv[1]
    # Load Jira credentials from environment
    jira_url = get_env_var("JIRA_URL")
    jira_email = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    jira = JiraAPI(jira_url, jira_email, jira_token)
    # Load field mapping if available
    field_mapping = {}
    if os.path.exists("jira_fields.json"):
        import json
        with open("jira_fields.json") as f:
            loaded = json.load(f)
            # If loaded is a list, convert to dict
            if isinstance(loaded, list):
                # Try to convert list of {name, id} dicts to mapping
                field_mapping = {item.get("name", item.get("field", "")): item.get("id", "") for item in loaded if isinstance(item, dict)}
            elif isinstance(loaded, dict):
                field_mapping = loaded
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            issue_key = row.get("Created Issue ID") or row.get("Issue Key")
            if not issue_key or issue_key.strip() == "":
                print(f"Skipping row with missing issue key: {row}")
                continue
            # Pass all fields from CSV to update function (preserve original keys)
            update_issue_fields(
                jira,
                issue_key,
                row.get("Story Points"),
                row.get("Original Estimate"),
                field_mapping,
                **{k: v for k, v in row.items() if k}
            )

if __name__ == "__main__":
    main()
