"""
merge_tracker_to_issues.py

Merge Story Points and Original Estimate from tracker.csv into my_issues_full.csv using Created Issue ID as key.
Output merged.csv, prompt user to review, then update Jira (excluding Time Spent).

Usage:
    python merge_tracker_to_issues.py
"""
import os
import sys
# Ensure .venv site-packages are in sys.path BEFORE any imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
venv_path = os.path.join(project_root, '.venv')
if os.path.isdir(venv_path):
    site_packages = None
    for root, dirs, files in os.walk(venv_path):
        for d in dirs:
            if d == 'site-packages':
                site_packages = os.path.join(root, d)
                break
        if site_packages:
            break
    if site_packages and site_packages not in sys.path:
        sys.path.insert(0, site_packages)
# Ensure project root is in sys.path for local imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import csv
from dotenv import load_dotenv
from jiraapi import JiraAPI

load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def merge_csvs(issues_path, tracker_path, merged_path):
    # Read tracker.csv into a dict keyed by Created Issue ID
    tracker = {}
    with open(tracker_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get('Created Issue ID') or row.get('Issue Key')
            if key:
                tracker[key] = row
    # Read my_issues_full.csv and create merged results (do not update original file)
    merged_rows = []
    with open(issues_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames if reader.fieldnames else []
        # Ensure 'Original Estimate' is present in fieldnames
        if 'Original Estimate' not in fieldnames:
            fieldnames.append('Original Estimate')
        for row in reader:
            merged_row = row.copy()
            key = row.get('Created Issue ID') or row.get('Issue Key')
            if key and key in tracker:
                # Always update Story Points from tracker
                merged_row['Story Points'] = tracker[key].get('Story Points', '')
                # Always add/update Original Estimate from tracker
                merged_row['Original Estimate'] = tracker[key].get('Original Estimate', '')
                print(f"Updated {key}: Story Points={merged_row['Story Points']}, Original Estimate={merged_row['Original Estimate']}")
            merged_rows.append(merged_row)
    # Write merged.csv
    with open(merged_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_rows:
            writer.writerow(row)
    print(f"Merged CSV written to {merged_path}. Please review before updating Jira.")

def update_jira_from_csv(merged_path):
    jira_url = get_env_var("JIRA_URL")
    jira_email = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    jira = JiraAPI(jira_url, jira_email, jira_token)
    with open(merged_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            issue_key = row.get('Created Issue ID') or row.get('Issue Key')
            if not issue_key:
                continue
            story_points = row.get('Story Points')
            original_estimate = row.get('Original Estimate')
            # Only update Story Points and Original Estimate
            update_fields = {}
            if story_points:
                update_fields['Story Points'] = story_points
            if original_estimate:
                update_fields['Original Estimate'] = original_estimate
            if update_fields:
                print(f"Updating {issue_key}: {update_fields}")
                # Call your update function here (adapt as needed)
                # Do NOT update Time Spent
                try:
                    # You may need to map field names to Jira field IDs here
                    # Example: jira.update_issue_fields(issue_key, story_points, original_estimate, field_mapping, **update_fields)
                    pass  # Replace with actual update logic
                except Exception as e:
                    print(f"Error updating {issue_key}: {e}")

def main():
    # Always resolve paths relative to project root
    issues_path = os.path.abspath(os.path.join(project_root, 'my_issues_full.csv'))
    tracker_path = os.path.abspath(os.path.join(project_root, 'output', 'tracker.csv'))
    merged_path = os.path.abspath(os.path.join(project_root, 'merged.csv'))
    merge_csvs(issues_path, tracker_path, merged_path)
    confirm = input("Review merged.csv. Type 'yes' to update Jira: ").strip().lower()
    if confirm == 'yes':
        update_jira_from_csv(merged_path)
    else:
        print("No updates made to Jira.")

if __name__ == "__main__":
    main()
