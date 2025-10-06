#!/usr/bin/env python3
"""
Fix script to set resolution to "Done" for closed but unresolved issues
"""
import os
import csv
from dotenv import load_dotenv
from jiraapi import JiraAPI

def fix_unresolved_closed_issues():
    """Fix issues that are closed but still marked as unresolved"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        print("Error: Missing environment variables")
        return False
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    # Check if output.csv exists to get list of created issues
    csv_files = ['output/output.csv', 'output/tracker.csv', 'merged.csv']
    issue_keys = []
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"Reading issue keys from {csv_file}")
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        issue_key = row.get('Created Issue ID') or row.get('Issue Key')
                        if issue_key and issue_key not in issue_keys:
                            issue_keys.append(issue_key)
                break
            except Exception as e:
                print(f"Could not read {csv_file}: {e}")
                continue
    
    if not issue_keys:
        print("No issue keys found in CSV files")
        issue_keys_input = input("Enter issue keys separated by commas (e.g., PROJ-1234,PROJ-1235): ").strip()
        if issue_keys_input:
            issue_keys = [key.strip() for key in issue_keys_input.split(',')]
        else:
            print("No issue keys provided. Exiting.")
            return False
    
    print(f"Found {len(issue_keys)} issues to check")
    print("=" * 50)
    
    unresolved_closed_issues = []
    
    # Check each issue
    for issue_key in issue_keys:
        try:
            issue = jira.get_issue(issue_key)
            status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
            resolution = issue.get("fields", {}).get("resolution")
            
            # Check if it's a closed status but unresolved
            closed_statuses = ["done", "closed", "complete", "resolved", "finished"]
            is_closed = status.lower() in closed_statuses
            is_unresolved = resolution is None
            
            if is_closed and is_unresolved:
                unresolved_closed_issues.append({
                    'key': issue_key,
                    'status': status
                })
                print(f"❌ {issue_key}: Status '{status}' but UNRESOLVED")
            elif is_closed:
                resolution_name = resolution.get("name", "Unknown") if resolution else "Unknown"
                print(f"✅ {issue_key}: Status '{status}' with resolution '{resolution_name}'")
            else:
                print(f"⏳ {issue_key}: Status '{status}' (not closed yet)")
                
        except Exception as e:
            print(f"❗ {issue_key}: Error checking status - {e}")
    
    print("=" * 50)
    print(f"Found {len(unresolved_closed_issues)} closed but unresolved issues")
    
    if unresolved_closed_issues:
        print("\nClosed but unresolved issues:")
        for issue in unresolved_closed_issues:
            print(f"  - {issue['key']}: {issue['status']}")
        
        fix_them = input(f"\nDo you want to set resolution to 'Done' for these {len(unresolved_closed_issues)} issues? (y/n): ").strip().lower()
        
        if fix_them == 'y':
            print("\nFixing resolutions...")
            fixed_count = 0
            failed_count = 0
            
            for issue in unresolved_closed_issues:
                issue_key = issue['key']
                try:
                    success = jira.set_resolution(issue_key, "Done")
                    if success:
                        print(f"✅ Fixed {issue_key}")
                        fixed_count += 1
                    else:
                        print(f"❌ Failed to fix {issue_key}")
                        failed_count += 1
                except Exception as e:
                    print(f"❌ Error fixing {issue_key}: {e}")
                    failed_count += 1
            
            print(f"\nResults: {fixed_count} fixed, {failed_count} failed")
        else:
            print("No changes made.")
    else:
        print("All closed issues already have proper resolutions!")
    
    return True

if __name__ == "__main__":
    print("Fix Unresolved Closed Issues")
    print("=" * 40)
    print("This script will:")
    print("1. Check all issues in your CSV files")
    print("2. Find issues that are closed but still 'Unresolved'")
    print("3. Optionally fix them by setting resolution to 'Done'")
    print()
    
    fix_unresolved_closed_issues()