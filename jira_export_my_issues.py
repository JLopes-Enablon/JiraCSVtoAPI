"""
jira_export_my_issues.py

Export all Jira issues assigned to or created by the current user to a local CSV, including all available fields.

Usage:
    python jira_export_my_issues.py [output_csv]

- Authenticates using .env variables
- Fetches all issues assigned to or created by you
- Extracts all available fields (standard + custom)
- Writes a CSV with all fields as columns
"""
import os
import csv
import logging
from dotenv import load_dotenv
from jiraapi import JiraAPI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def flatten_fields(fields):
    flat = {}
    for k, v in fields.items():
        if isinstance(v, dict):
            for subk, subv in v.items():
                flat[f"{k}.{subk}"] = subv
        else:
            flat[k] = v
    return flat

def main():
    import sys
    load_dotenv()
    logging.basicConfig(filename="error.log", level=logging.ERROR)
    if len(sys.argv) < 2:
        print("Usage: python jira_export_my_issues.py [output_csv]")
        return
    output_csv = sys.argv[1]
    jira_url = get_env_var("JIRA_URL")
    jira_email = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    jira = JiraAPI(jira_url, jira_email, jira_token)
    # JQL for issues assigned to or reported by current user
    jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"
    url = f"{jira.base_url}/rest/api/3/search"
    params = {"jql": jql, "maxResults": 1000, "expand": "names"}
    resp = jira.session.get(url, params=params)
    if not resp.ok:
        print(f"Jira API error: {resp.status_code} {resp.text}")
        return
    data = resp.json()
    issues = data.get("issues", [])
    if not issues:
        print("No issues found for current user.")
        return
    # Collect all field names
    all_fieldnames = set()
    flat_issues = []
    for issue in issues:
        fields = flatten_fields(issue.get("fields", {}))
        fields["Key"] = issue.get("key")
        flat_issues.append(fields)
        all_fieldnames.update(fields.keys())
    fieldnames = sorted(all_fieldnames)
    # Write CSV
    with open(output_csv, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for fields in flat_issues:
            writer.writerow({k: fields.get(k, "") for k in fieldnames})
    print(f"Exported {len(flat_issues)} issues to {output_csv}")

if __name__ == "__main__":
    main()
