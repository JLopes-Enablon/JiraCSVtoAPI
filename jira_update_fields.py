"""
jira_update_fields.py

Update missing custom fields (e.g., Story Points, Original Estimate) for existing Jira issues listed in a CSV/output file.

Usage:
    python jira_update_fields.py [input_csv]

- Reads issue keys and field values from the CSV.
- Updates only missing or errored fields for each issue.
- Skips issues without a valid Jira key.
- Logs errors to error.log.
"""
import os
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
    # Map CSV fields to Jira fields
    csv_to_jira = {
        "Summary": "summary",
        "Priority": "priority",
        "Start Date": field_mapping.get("Start Date", "customfield_10257"),
        "Story Points": "customfield_10016",  # Corrected to use the editable field
        "Original Estimate": "timetracking",
    }
    # Compare and update all fields
    for csv_field, jira_field in csv_to_jira.items():
        csv_value = kwargs.get(csv_field.replace(" ", "_"))
        if csv_value is None:
            continue
        # Priority is a dict in Jira
        if csv_field == "Priority":
            if csv_value and (not current_fields.get("priority") or csv_value != current_fields["priority"].get("name")):
                update_fields["priority"] = {"name": csv_value}
        elif csv_field == "Original Estimate":
            jira_estimate = current_fields.get("timetracking", {}).get("originalEstimate")
            if csv_value and csv_value != jira_estimate:
                update_fields["timetracking"] = {"originalEstimate": csv_value}
        else:
            jira_val = current_fields.get(jira_field)
            if csv_value and str(csv_value) != str(jira_val):
                update_fields[jira_field] = csv_value
    # Also check and update Time Spent (worklog)
    time_spent = kwargs.get("Time_spent")
    if time_spent:
        # Always log work, cannot compare
        try:
            jira.log_work(issue_key, time_spent)
            print(f"Logged work for {issue_key}: {time_spent}")
        except Exception as e:
            logging.error(f"Failed to log work for {issue_key}: {e}")
            errors.append(str(e))
    if update_fields:
        print(f"Attempting update for {issue_key}: {update_fields}")
        try:
            jira.session.put(f"{jira.base_url}/rest/api/3/issue/{issue_key}", json={"fields": update_fields})
            print(f"Updated {issue_key}: {list(update_fields.keys())}")
        except Exception as e:
            logging.error(f"Failed to update {issue_key}: {e}")
            errors.append(str(e))
    else:
        print(f"No update needed for {issue_key}")
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
            # Pass all fields from CSV to update function
            update_issue_fields(
                jira,
                issue_key,
                row.get("Story Points"),
                row.get("Original Estimate"),
                field_mapping,
                Summary=row.get("Summary"),
                Priority=row.get("Priority"),
                Start_Date=row.get("Start Date"),
                Time_spent=row.get("Time spent"),
                Parent=row.get("Parent"),
                IssueType=row.get("IssueType"),
                Project=row.get("Project")
            )

if __name__ == "__main__":
    main()
