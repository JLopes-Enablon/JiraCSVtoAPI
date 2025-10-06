"""
update_estimate_and_transition.py - Bulk update Jira Original Estimate and transition issues to Done

Reads tracker.csv, updates only the Original Estimate field, and transitions each work item from To Do to Done.

Usage:
    python Tools/update_estimate_and_transition.py [--csv path/to/tracker.csv]

Requirements:
- JIRA_URL, JIRA_USER, JIRA_API_TOKEN in .env or environment variables
- tracker.csv must have columns: Issue Key, Original Estimate (or similar)

"""

import os
import sys
import csv
import requests
import time
from dotenv import load_dotenv
import argparse

# Explicitly load .env from project root for reliability
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
print(f"[DEBUG] Loading .env from: {env_path}")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()



# Helper to strip quotes from env vars
def strip_quotes(val):
    if val and ((val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"'))):
        return val[1:-1]
    return val


JIRA_URL = strip_quotes(os.getenv('JIRA_URL'))
JIRA_EMAIL = strip_quotes(os.getenv('JIRA_EMAIL'))
JIRA_TOKEN = strip_quotes(os.getenv('JIRA_TOKEN'))
JIRA_ASSIGNEE = strip_quotes(os.getenv('JIRA_ASSIGNEE'))  # Only used for assigning, not for auth

print(f"[DEBUG] JIRA_URL={JIRA_URL!r}, JIRA_EMAIL={JIRA_EMAIL!r}, JIRA_TOKEN={'SET' if JIRA_TOKEN else 'NOT SET'}")

if not all([JIRA_URL, JIRA_EMAIL, JIRA_TOKEN]):
    print("Error: JIRA_URL, JIRA_EMAIL, and JIRA_TOKEN must be set in .env or environment.")
    sys.exit(1)

HEADERS = {
    "Content-Type": "application/json"
}
AUTH = (JIRA_EMAIL, JIRA_TOKEN)

# Map possible column names for issue key and estimate
ISSUE_KEY_COLS = ["Issue Key", "Key", "Issue", "IssueID", "Created Issue ID"]
ESTIMATE_COLS = ["Original Estimate", "OriginalEstimate", "Estimate"]

# Find the transition ID for 'Done' for a given issue
def get_done_transition_id(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = requests.get(url, headers=HEADERS, auth=AUTH)
    if resp.status_code != 200:
        print(f"  [!] Could not fetch transitions for {issue_key}: {resp.text}")
        return None
    transitions = resp.json().get('transitions', [])
    for t in transitions:
        if t['name'].lower() == 'done':
            return t['id']
    return None

# Update the Original Estimate field
def update_original_estimate(issue_key, estimate):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"
    # Update both timetracking.originalEstimate and priority to Medium
    data = {
        "fields": {
            "timetracking": {
                "originalEstimate": estimate
            },
            "priority": {"name": "Medium"}
        }
    }
    resp = requests.put(url, json=data, headers=HEADERS, auth=AUTH)
    if resp.status_code == 204:
        return True
    else:
        print(f"  [!] Failed to update estimate/priority for {issue_key}: {resp.text}")
        return False

# Transition the issue to Done
def transition_to_done(issue_key):
    transition_id = get_done_transition_id(issue_key)
    if not transition_id:
        print(f"  [!] No 'Done' transition found for {issue_key}")
        return False
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    data = {"transition": {"id": transition_id}}
    resp = requests.post(url, json=data, headers=HEADERS, auth=AUTH)
    if resp.status_code == 204:
        return True
    else:
        print(f"  [!] Failed to transition {issue_key} to Done: {resp.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Bulk update Jira Original Estimate and transition to Done from a CSV file")
    parser.add_argument('--csv', default="Backup output.csv", help="Path to source CSV (default: Backup output.csv)")
    parser.add_argument('--limit', type=int, default=None, help="Limit to N work items (for testing)")
    args = parser.parse_args()

    csv_path = args.csv
    limit = args.limit
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    import datetime
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Find the correct column names
        header = reader.fieldnames
        issue_col = next((c for c in ISSUE_KEY_COLS if c in header), None)
        estimate_col = next((c for c in ESTIMATE_COLS if c in header), None)
        # Try to find a date column
        date_cols = [c for c in header if 'date' in c.lower()]
        date_col = date_cols[0] if date_cols else None
        if not issue_col or not estimate_col or not date_col:
            print(f"Error: Could not find required columns in CSV. Found: {header}")
            print("Required: issue key, estimate, and a date column (e.g., 'Start Date').")
            sys.exit(1)
        print(f"Processing {csv_path} (only July work items)...\n")
        processed = 0
        for row in reader:
            if limit is not None and processed >= limit:
                break
            issue_key = row[issue_col].strip()
            estimate = row[estimate_col].strip()
            date_str = row[date_col].strip()
            if not issue_key or not estimate or not date_str:
                continue
            # Try to parse the date (support yyyy-mm-dd and dd/mm/yy or dd/mm/yyyy)
            month = None
            try:
                if '-' in date_str:
                    # yyyy-mm-dd
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    month = dt.month
                elif '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts[2]) == 2:
                        # dd/mm/yy
                        dt = datetime.datetime.strptime(date_str, '%d/%m/%y')
                    else:
                        # dd/mm/yyyy
                        dt = datetime.datetime.strptime(date_str, '%d/%m/%Y')
                    month = dt.month
            except Exception as e:
                print(f"  [!] Could not parse date '{date_str}' for {issue_key}: {e}")
                continue
            if month != 7:
                continue  # Only process July
            print(f"Updating {issue_key}: Estimate='{estimate}' ...", end='')
            ok1 = update_original_estimate(issue_key, estimate)
            if ok1:
                print(" estimate updated.", end='')
            ok2 = transition_to_done(issue_key)
            if ok2:
                print(" transitioned to Done.", end='')
            print()
            processed += 1
            time.sleep(0.5)  # Avoid hitting rate limits
    print("\nAll done.")

if __name__ == "__main__":
    main()
