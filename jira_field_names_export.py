"""
jira_field_names_export.py

Export all Jira field metadata (ID, display name, description) to a CSV for mapping and review.

Usage:
    python jira_field_names_export.py [output_csv]

- Authenticates using .env variables
- Fetches all field metadata from Jira
- Writes a CSV with Field ID, Display Name, Description
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

def main():
    import sys
    load_dotenv()
    logging.basicConfig(filename="error.log", level=logging.ERROR)
    if len(sys.argv) < 2:
        print("Usage: python jira_field_names_export.py [output_csv]")
        return
    output_csv = sys.argv[1]
    jira_url = get_env_var("JIRA_URL")
    jira_email = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    jira = JiraAPI(jira_url, jira_email, jira_token)
    url = f"{jira.base_url}/rest/api/3/field"
    resp = jira.session.get(url)
    if not resp.ok:
        print(f"Jira API error: {resp.status_code} {resp.text}")
        return
    fields = resp.json()
    with open(output_csv, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "name", "description"])
        writer.writeheader()
        for field in fields:
            writer.writerow({
                "id": field.get("id", ""),
                "name": field.get("name", ""),
                "description": field.get("description", "")
            })
    print(f"Exported {len(fields)} field names to {output_csv}")

if __name__ == "__main__":
    main()
