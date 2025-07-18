"""
jira_export_my_issues.py

Export all Jira issues assigned to or created by the current user to a local CSV, 
using only the fields that match the output.csv format.

Usage:
    python jira_export_my_issues.py [output_csv]

- Authenticates using .env variables
- Fetches ALL issues assigned to or created by you using automatic pagination
- Extracts only the specific fields used in output.csv:
  Project, Summary, IssueType, Parent, Start Date, Story Points, 
  Original Estimate, Time spent, Priority, Created Issue ID
- Writes a CSV with these fields as columns in the same order
- Automatically handles large result sets by fetching issues in batches of 100
"""
import os
import csv
import logging
import sys
import os
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from dotenv import load_dotenv
from jiraapi import JiraAPI

def flatten_field(val):
    """Flatten dict/list field to a readable string for CSV export."""
    if isinstance(val, dict):
        # Try common display keys
        for k in ["name", "key", "value", "summary"]:
            if k in val:
                return str(val[k])
        # If none found, return str
        return str(val)
    elif isinstance(val, list):
        # Try to flatten each item
        return ", ".join([flatten_field(v) for v in val])
    return str(val)

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def format_time_seconds(seconds):
    if not seconds:
        return ""
    try:
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{total_seconds}s"
    except (ValueError, TypeError):
        return str(seconds)

def extract_required_fields(issue):
    """Extract only the fields used in output.csv format, flattening all values."""
    fields = issue.get("fields", {})
    extracted = {
        "Project": flatten_field(fields.get("project", {}).get("key", "")) if fields.get("project") else "",
        "Summary": flatten_field(fields.get("summary", "")),
        "IssueType": flatten_field(fields.get("issuetype", {}).get("name", "")) if fields.get("issuetype") else "",
        "Parent": flatten_field(fields.get("parent", {}).get("key", "")) if fields.get("parent") else "",
        "Start Date": flatten_field(fields.get("customfield_10015", "")),
        "Story Points": flatten_field(fields.get("customfield_10146", "")),
        "Original Estimate": flatten_field(fields.get("timeoriginalestimate", "")),
        "Time spent": flatten_field(fields.get("timespent", "")),
        "Priority": flatten_field(fields.get("priority", {}).get("name", "")) if fields.get("priority") else "",
        "Created Issue ID": flatten_field(issue.get("key", ""))
    }
    # Format time fields to match output.csv format
    if extracted["Original Estimate"]:
        extracted["Original Estimate"] = format_time_seconds(extracted["Original Estimate"])
    if extracted["Time spent"]:
        extracted["Time spent"] = format_time_seconds(extracted["Time spent"])
    return extracted
    
def extract_all_fields(issue):
    """Extract all available fields from the issue, flattening all values."""
    fields = issue.get("fields", {})
    extracted = {k: flatten_field(v) for k, v in fields.items()}
    extracted["Created Issue ID"] = flatten_field(issue.get("key", ""))
    return extracted

def fetch_all_issues(jira, jql):
    """Fetch all issues using pagination to handle large result sets"""
    all_issues = []
    start_at = 0
    max_results = 100  # Jira's recommended page size
    total_fetched = 0
    
    print("Fetching issues from Jira...")
    
    while True:
        url = f"{jira.base_url}/rest/api/3/search"
        params = {
            "jql": jql, 
            "maxResults": max_results, 
            "startAt": start_at,
            "expand": "names"
        }
        
        resp = jira.session.get(url, params=params)
        if not resp.ok:
            print(f"Jira API error: {resp.status_code} {resp.text}")
            return []
        
        data = resp.json()
        issues = data.get("issues", [])
        total = data.get("total", 0)
        
        if not issues:
            break
        
        all_issues.extend(issues)
        total_fetched += len(issues)
        
        print(f"Fetched {total_fetched} of {total} issues...")
        
        # Check if we've fetched all available issues
        if total_fetched >= total or len(issues) < max_results:
            break
        
        start_at += max_results
    
    print(f"Completed: Fetched {total_fetched} total issues")
    return all_issues

def main():
    import sys
    load_dotenv()
    logging.basicConfig(filename="error.log", level=logging.ERROR)

    # Interactive prompt if arguments are missing
    if len(sys.argv) < 2:
        output_csv = input("Enter filename for export (or press Enter for 'output.csv'): ").strip()
        if not output_csv:
            output_csv = "output.csv"
    else:
        output_csv = sys.argv[1]

    if len(sys.argv) < 3:
        print("Select export mode:")
        print("1. Export focused fields (recommended for bulk transitions)")
        print("2. Export all available fields (comprehensive review)")
        mode = input("Enter mode (1 or 2): ").strip()
        if mode not in ["1", "2"]:
            print("Invalid mode. Defaulting to 1.")
            mode = "1"
    else:
        mode = sys.argv[2].strip()
    jira_url = get_env_var("JIRA_URL")
    jira_user = get_env_var("JIRA_EMAIL")
    jira_token = get_env_var("JIRA_TOKEN")
    jira = JiraAPI(jira_url, jira_user, jira_token)

    # JQL for issues assigned to or reported by current user
    jql = "assignee = currentUser() OR reporter = currentUser() ORDER BY updated DESC"

    # Fetch all issues using pagination
    issues = fetch_all_issues(jira, jql)

    if not issues:
        print("No issues found for current user.")
        return

    extracted_issues = []
    # Extract only the required fields from each issue
    if mode == "2":
        # Load editable field ids and display names from jira_field_names.csv
        editable_fields = []  # List of (id, name) tuples
        import csv as _csv
        editable_csv_path = os.path.join(project_root, "jira_field_names.csv")
        with open(editable_csv_path, newline='', encoding='utf-8') as f:
            reader = _csv.DictReader(f)
            for row in reader:
                if row.get("editable", "False").strip().lower() == "true":
                    editable_fields.append((row["id"], row["name"]))
        # Export only editable fields (by id), but use display names as headers
        field_ids = [fid for fid, _ in editable_fields]
        fieldnames = [name for _, name in editable_fields]
        # Ensure 'Created Issue ID' is always present as last column
        if "Created Issue ID" not in fieldnames:
            fieldnames.append("Created Issue ID")
        for issue in issues:
            all_fields = extract_all_fields(issue)
            filtered_fields = {}
            for fid, name in editable_fields:
                filtered_fields[name] = flatten_field(all_fields.get(fid, ""))
            # Always add Created Issue ID
            filtered_fields["Created Issue ID"] = flatten_field(issue.get("key", ""))
            extracted_issues.append(filtered_fields)
    else:
        # Export only output.csv fields
        for issue in issues:
            extracted_issues.append(extract_required_fields(issue))
        fieldnames = [
            "Project", "Summary", "IssueType", "Parent", "Start Date", 
            "Story Points", "Original Estimate", "Time spent", "Priority", "Created Issue ID"
        ]

    # Write CSV
    with open(output_csv, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for fields in extracted_issues:
            writer.writerow(fields)

    print(f"Exported {len(extracted_issues)} issues to {output_csv} (mode {mode})")

if __name__ == "__main__":
    main()