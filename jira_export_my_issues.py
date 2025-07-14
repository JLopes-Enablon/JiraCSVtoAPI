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
from dotenv import load_dotenv
from jiraapi import JiraAPI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def format_time_seconds(seconds):
    """Convert seconds to human readable format like '1h 30m' or '45m'"""
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
    """Extract only the fields used in output.csv format"""
    fields = issue.get("fields", {})
    
    # Extract specific fields matching output.csv structure
    extracted = {
        "Project": fields.get("project", {}).get("key", "") if fields.get("project") else "",
        "Summary": fields.get("summary", ""),
        "IssueType": fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else "",
        "Parent": fields.get("parent", {}).get("key", "") if fields.get("parent") else "",
        "Start Date": fields.get("customfield_10015", ""),  # Start Date custom field
        "Story Points": fields.get("customfield_10016", ""),  # Story Points custom field
        "Original Estimate": fields.get("timeoriginalestimate", ""),
        "Time spent": fields.get("timespent", ""),
        "Priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
        "Created Issue ID": issue.get("key", "")
    }
    
    # Format time fields to match output.csv format
    if extracted["Original Estimate"]:
        extracted["Original Estimate"] = format_time_seconds(extracted["Original Estimate"])
    if extracted["Time spent"]:
        extracted["Time spent"] = format_time_seconds(extracted["Time spent"])
    
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
    
    # Fetch all issues using pagination
    issues = fetch_all_issues(jira, jql)
    
    if not issues:
        print("No issues found for current user.")
        return
    
    # Extract only the required fields from each issue
    extracted_issues = []
    for issue in issues:
        extracted_fields = extract_required_fields(issue)
        extracted_issues.append(extracted_fields)
    
    # Define the fieldnames in the same order as output.csv
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
    
    print(f"Exported {len(extracted_issues)} issues to {output_csv}")

if __name__ == "__main__":
    main()