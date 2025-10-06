#!/usr/bin/env python3
"""
Debug script to test transition and resolution setting with real Jira issues
"""
import os
import json
from dotenv import load_dotenv
from jiraapi import JiraAPI

def debug_issue_transitions(issue_key):
    """Debug what transitions and resolutions are available for an issue"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        print("Error: Missing environment variables")
        return False
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print(f"Debugging issue: {issue_key}")
    print("=" * 50)
    
    try:
        # Get current issue status
        issue = jira.get_issue(issue_key)
        current_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        current_resolution = issue.get("fields", {}).get("resolution")
        resolution_name = current_resolution.get("name") if current_resolution else "Unresolved"
        
        print(f"Current Status: {current_status}")
        print(f"Current Resolution: {resolution_name}")
        print()
        
        # Get available transitions
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = jira.session.get(url)
        if resp.ok:
            transitions_data = resp.json()
            transitions = transitions_data.get("transitions", [])
            
            print("Available Transitions:")
            for transition in transitions:
                trans_name = transition.get("name", "Unknown")
                trans_id = transition.get("id", "Unknown")
                trans_fields = transition.get("fields", {})
                
                print(f"  - {trans_name} (ID: {trans_id})")
                
                # Check if resolution is available in this transition
                if "resolution" in trans_fields:
                    resolution_field = trans_fields["resolution"]
                    allowed_values = resolution_field.get("allowedValues", [])
                    print(f"    Resolution options: {[r.get('name', 'Unknown') for r in allowed_values]}")
                else:
                    print(f"    No resolution field in this transition")
        else:
            print(f"Failed to get transitions: {resp.status_code} {resp.text}")
        
        print()
        
        # Get available resolutions through editmeta
        print("Available Resolutions (via editmeta):")
        resolutions = jira.get_available_resolutions(issue_key)
        if resolutions:
            for res in resolutions:
                print(f"  - {res.get('name', 'Unknown')} (ID: {res.get('id', 'Unknown')})")
        else:
            print("  No resolutions available or field not editable")
            
    except Exception as e:
        print(f"Error debugging issue {issue_key}: {e}")
        return False
    
    return True

def test_resolution_setting(issue_key):
    """Test setting resolution on an issue"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print(f"\nTesting resolution setting for: {issue_key}")
    print("=" * 50)
    
    # Don't actually change anything, just test the logic
    try:
        resolutions = jira.get_available_resolutions(issue_key)
        if resolutions:
            print("✓ Resolution field is editable")
            print(f"Available resolutions: {[r.get('name') for r in resolutions]}")
            
            # Find "Done" resolution
            done_resolution = next((r for r in resolutions if r.get("name", "").lower() == "done"), None)
            if done_resolution:
                print("✓ 'Done' resolution is available")
            else:
                print("✗ 'Done' resolution not found, would use fallback")
        else:
            print("✗ Resolution field is not editable for this issue")
            
    except Exception as e:
        print(f"Error testing resolution: {e}")

if __name__ == "__main__":
    print("Jira Transition and Resolution Debug Tool")
    print("=" * 60)
    
    # You can specify an issue key to debug, or we'll use a default
    test_issue = input("Enter an issue key to debug (or press Enter to skip): ").strip()
    
    if test_issue:
        success = debug_issue_transitions(test_issue)
        if success:
            test_resolution_setting(test_issue)
    else:
        print("No issue key provided. Skipping debug test.")
        print("\nTo debug a specific issue, run:")
        print("python debug_transitions.py")
        print("and enter an issue key like 'PROJ-1234'")