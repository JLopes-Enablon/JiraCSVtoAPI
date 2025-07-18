import sys
import os
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
"""
jira_bulk_transition.py

Bulk transition Jira issues to completion status using a CSV file as input.
Automatically determines the correct target status based on issue type:
- Epics, Stories: "Closed"
- Tasks, Sub-tasks: "Done"

Usage:
    python jira_bulk_transition.py [csv_file] [optional_target_status]

- Reads CSV file with "Created Issue ID" and "IssueType" columns
- Auto-selects correct completion status based on issue type
- Logs all transitions and any failures
- Provides progress tracking and summary report

Examples:
    python jira_bulk_transition.py my_exported_issues_all.csv
    python jira_bulk_transition.py my_exported_issues_all.csv "Done"  # Force all to Done
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

def get_target_status_for_issue_type(issue_type):
    """
    Determine the appropriate target status based on issue type.
    Args:
        issue_type: The Jira issue type (e.g., 'Story', 'Sub-task', 'Epic', 'Task')
    Returns:
        The appropriate target status string
    """
    issue_type_lower = issue_type.lower()
    
    # Epic and Story types typically transition to "Closed"
    if issue_type_lower in ['epic', 'story']:
        return "Closed"
    
    # Task and Sub-task types typically transition to "Done"
    elif issue_type_lower in ['task', 'sub-task', 'subtask']:
        return "Done"
    
    # Default to "Done" for unknown types
    else:
        return "Done"

def read_issues_from_csv(csv_file):
    """Read issue keys from CSV file"""
    issues = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                issue_key = row.get('Created Issue ID', '').strip()
                if issue_key:
                    issues.append({
                        'key': issue_key,
                        'summary': row.get('Summary', ''),
                        'issue_type': row.get('IssueType', '')
                    })
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
    
    return issues

def bulk_transition_issues(jira, issues, force_target_status=None):
    """Transition multiple issues to appropriate completion status"""
    successful_transitions = []
    failed_transitions = []
    skipped_transitions = []
    
    total_issues = len(issues)
    print(f"Starting bulk transition of {total_issues} issues to completion status...")
    
    # Group issues by target status for summary
    status_groups = {}
    
    for i, issue_data in enumerate(issues, 1):
        issue_key = issue_data['key']
        issue_summary = issue_data['summary']
        issue_type = issue_data['issue_type']
        
        # Determine target status
        if force_target_status:
            target_status = force_target_status
        else:
            target_status = get_target_status_for_issue_type(issue_type)
        
        # Track status groups for summary
        if target_status not in status_groups:
            status_groups[target_status] = 0
        status_groups[target_status] += 1
        
        print(f"Processing {i}/{total_issues}: {issue_key} ({issue_type} → {target_status}) - {issue_summary[:40]}...")
        
        try:
            # Try to transition the issue
            result = jira.transition_issue(issue_key, target_status)
            
            if result:
                successful_transitions.append({
                    'key': issue_key,
                    'summary': issue_summary,
                    'issue_type': issue_type,
                    'target_status': target_status,
                    'message': f"Successfully transitioned to {target_status}"
                })
                print(f"  ✅ Success: {issue_key} → {target_status}")
            else:
                # Check if issue is already in target status
                current_status = jira.get_issue_status(issue_key)
                if current_status and current_status.lower() == target_status.lower():
                    skipped_transitions.append({
                        'key': issue_key,
                        'summary': issue_summary,
                        'issue_type': issue_type,
                        'target_status': target_status,
                        'message': f"Already in {target_status} status"
                    })
                    print(f"  ⏭️  Skipped: {issue_key} (already {current_status})")
                else:
                    failed_transitions.append({
                        'key': issue_key,
                        'summary': issue_summary,
                        'issue_type': issue_type,
                        'target_status': target_status,
                        'message': f"Failed to transition from {current_status} to {target_status}"
                    })
                    print(f"  ❌ Failed: {issue_key} (current: {current_status}, wanted: {target_status})")
                    
        except Exception as e:
            failed_transitions.append({
                'key': issue_key,
                'summary': issue_summary,
                'issue_type': issue_type,
                'target_status': target_status,
                'message': f"Error: {str(e)}"
            })
            print(f"  ❌ Error: {issue_key} - {str(e)}")
            logging.error(f"Error transitioning {issue_key}: {str(e)}")
    
    # Print status group summary
    print(f"\nTransition targets by issue type:")
    for status, count in status_groups.items():
        print(f"  → {status}: {count} issues")
    
    return successful_transitions, failed_transitions, skipped_transitions

def save_transition_report(successful, failed, skipped):
    """Save detailed transition report to CSV"""
    report_filename = f"transition_report.csv"
    
    with open(report_filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['Issue Key', 'Summary', 'Issue Type', 'Target Status', 'Result', 'Message']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write successful transitions
        for item in successful:
            writer.writerow({
                'Issue Key': item['key'],
                'Summary': item['summary'],
                'Issue Type': item['issue_type'],
                'Target Status': item['target_status'],
                'Result': 'Success',
                'Message': item['message']
            })
        
        # Write skipped transitions
        for item in skipped:
            writer.writerow({
                'Issue Key': item['key'],
                'Summary': item['summary'],
                'Issue Type': item['issue_type'],
                'Target Status': item['target_status'],
                'Result': 'Skipped',
                'Message': item['message']
            })
        
        # Write failed transitions
        for item in failed:
            writer.writerow({
                'Issue Key': item['key'],
                'Summary': item['summary'],
                'Issue Type': item['issue_type'],
                'Target Status': item['target_status'],
                'Result': 'Failed',
                'Message': item['message']
            })
    
    print(f"\nDetailed report saved to: {report_filename}")

def main():
    """Main function to handle command line arguments and execute bulk transition"""
    import sys
    load_dotenv()
    logging.basicConfig(filename="error.log", level=logging.ERROR, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python jira_bulk_transition.py <csv_file> [target_status]")
        print("")
        print("If target_status is not provided, the script will automatically")
        print("select the appropriate completion status based on issue type:")
        print("  - Epic, Story → Closed")
        print("  - Task, Sub-task → Done")
        print("")
        print("Examples:")
        print("  python jira_bulk_transition.py output.csv")
        print("  python jira_bulk_transition.py output.csv Closed")
        return
    
    csv_file = sys.argv[1]
    force_target_status = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate inputs
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' does not exist.")
        return
    
    # Get Jira credentials
    try:
        jira_url = get_env_var("JIRA_URL")
        jira_email = get_env_var("JIRA_EMAIL")
        jira_token = get_env_var("JIRA_TOKEN")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Initialize Jira connection
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    # Read issues from CSV
    print(f"Reading issues from: {csv_file}")
    issues = read_issues_from_csv(csv_file)
    
    if not issues:
        print("No issues found in CSV file.")
        return
    
    print(f"Found {len(issues)} issues to process.")
    
    if force_target_status:
        print(f"Using forced target status: {force_target_status}")
        confirm_msg = f"transition {len(issues)} issues to '{force_target_status}'"
    else:
        print("Using automatic status detection based on issue type:")
        print("  - Epic, Story → Closed")
        print("  - Task, Sub-task → Done")
        confirm_msg = f"transition {len(issues)} issues using automatic status detection"
    
    # Confirm before proceeding
    confirm = input(f"\nAre you sure you want to {confirm_msg}? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Perform bulk transition
    successful, failed, skipped = bulk_transition_issues(jira, issues, force_target_status)
    
    # Print summary
    print("\n" + "="*60)
    print("BULK TRANSITION SUMMARY")
    print("="*60)
    print(f"Total issues processed: {len(issues)}")
    print(f"✅ Successfully transitioned: {len(successful)}")
    print(f"⏭️  Skipped (already in target status): {len(skipped)}")
    print(f"❌ Failed transitions: {len(failed)}")
    
    if failed:
        print(f"\nFailed issues:")
        for item in failed:
            print(f"  - {item['key']}: {item['message']}")
    
    # Save detailed report
    save_transition_report(successful, failed, skipped)
    
    print(f"\nBulk transition completed!")

if __name__ == "__main__":
    main()
