#!/usr/bin/env python3
"""
Create a test issue and analyze its workflow from the beginning
"""
import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_new_issue_workflow():
    """Create a new issue and test the workflow"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    if not all([jira_url, jira_email, jira_token]):
        print("Error: Missing environment variables")
        return
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("Creating Test Issue to Analyze Workflow")
    print("=" * 50)
    
    try:
        # Create a test issue
        test_issue = jira.create_issue(
            project_key=project_id,
            summary="TEST - Resolution Workflow Analysis (DELETE AFTER TESTING)",
            issue_type="Task",
            assignee=None
        )
        
        issue_key = test_issue["key"]
        print(f"✓ Created test issue: {issue_key}")
        print()
        
        # Analyze its workflow
        print("Analyzing workflow for new issue...")
        print("-" * 40)
        
        # Get current status
        issue = jira.get_issue(issue_key)
        current_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        print(f"Initial Status: {current_status}")
        print()
        
        # Get available transitions
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = jira.session.get(url)
        if resp.ok:
            transitions = resp.json().get("transitions", [])
            
            print("Available Transitions from Initial Status:")
            closing_transitions_with_resolution = []
            
            for i, transition in enumerate(transitions, 1):
                trans_name = transition.get("name", "Unknown")
                to_status = transition.get("to", {}).get("name", "Unknown")
                trans_fields = transition.get("fields", {})
                
                print(f"{i}. {trans_name} → {to_status}")
                
                # Check if this leads to a closed state AND has resolution
                is_closing = any(keyword in to_status.lower() for keyword in 
                               ["done", "closed", "complete", "resolve", "finish"])
                has_resolution = "resolution" in trans_fields
                
                if has_resolution:
                    resolution_options = trans_fields["resolution"].get("allowedValues", [])
                    resolution_names = [r.get('name', 'Unknown') for r in resolution_options]
                    required = trans_fields["resolution"].get("required", False)
                    print(f"   → Has resolution field (required: {required})")
                    print(f"   → Resolution options: {resolution_names}")
                    
                    if is_closing:
                        closing_transitions_with_resolution.append({
                            'name': trans_name,
                            'to_status': to_status,
                            'resolutions': resolution_names,
                            'required': required
                        })
                else:
                    print(f"   → No resolution field")
                print()
            
            # Show results
            if closing_transitions_with_resolution:
                print("✓ Found closing transitions with resolution:")
                for trans in closing_transitions_with_resolution:
                    print(f"  - {trans['name']} → {trans['to_status']}")
                    print(f"    Resolutions: {trans['resolutions']}")
                    print(f"    Required: {trans['required']}")
                print()
                print("✓ This workflow supports proper resolution setting!")
            else:
                print("✗ No closing transitions with resolution found")
                print("  This means resolution must be set differently")
        
        # Ask user what to do with test issue
        print("-" * 40)
        choice = input(f"What to do with test issue {issue_key}?\n1. Delete it\n2. Keep it for further testing\nChoice [1]: ").strip()
        
        if choice != "2":
            print("Note: You should manually delete the test issue from Jira UI")
            print(f"Test issue: {issue_key}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_new_issue_workflow()