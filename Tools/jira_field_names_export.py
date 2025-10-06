"""
jira_field_names_export.py

Export all Jira field metadata (ID, display name, description) to a CSV for mapping and review.

Usage:
    python jira_field_names_export.py [output_csv]

"""
import os
import csv
import logging
import sys
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from dotenv import load_dotenv
from jiraapi import JiraAPI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    # Strip single or double quotes if present
    if isinstance(value, str):
        value = value.strip('"').strip("'")
    return value

def main():
    import sys
    # Explicitly load .env from project root
    env_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=env_path)
    logging.basicConfig(filename="error.log", level=logging.ERROR)
    if len(sys.argv) < 2:
        output_csv = "Jira_Metadata.csv"
        print("No output filename provided. Defaulting to 'Jira_Metadata.csv'.")
    else:
        output_csv = sys.argv[1]

    # Prompt for sample issue key for editmeta
    if len(sys.argv) < 3:
        issue_key = input("Enter a sample issue key to check editable fields (e.g. PROJ-123): ").strip()
    else:
        issue_key = sys.argv[2].strip()
    jira_url = get_env_var("JIRA_URL")
    jira_email = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    print(f"SAFE DEBUG: JIRA_URL loaded: {jira_url is not None}, type: {type(jira_url).__name__}")
    print(f"SAFE DEBUG: JIRA_EMAIL loaded: {jira_email is not None}, type: {type(jira_email).__name__}")
    print(f"SAFE DEBUG: JIRA_TOKEN loaded: {jira_token is not None}, type: {type(jira_token).__name__}")
    jira = JiraAPI(jira_url, jira_email, jira_token)
    # Get all fields metadata
    url = f"{jira.base_url}/rest/api/3/field"
    resp = jira.session.get(url)
    if not resp.ok:
        print(f"Jira API error: {resp.status_code} {resp.text}")
        return
    fields = resp.json()

    # Query editmeta for the sample issue
    editmeta_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/editmeta"
    editmeta_resp = jira.session.get(editmeta_url)
    if not editmeta_resp.ok:
        print(f"Jira editmeta API error: {editmeta_resp.status_code} {editmeta_resp.text}")
        editable_fields = set()
    else:
        editmeta = editmeta_resp.json()
        editable_fields = set(editmeta.get("fields", {}).keys())

    # Write only editable fields to CSV
    with open(output_csv, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "name", "description", "editable"])
        writer.writeheader()
        editable_count = 0
        for field in fields:
            field_id = field.get("id", "")
            if field_id in editable_fields:
                writer.writerow({
                    "id": field_id,
                    "name": field.get("name", ""),
                    "description": field.get("description", ""),
                    "editable": "True"
                })
                editable_count += 1
    print(f"Exported {editable_count} editable field names to {output_csv}")

if __name__ == "__main__":
    main()
