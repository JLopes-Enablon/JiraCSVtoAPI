#!/usr/bin/env python3
"""
Test and fix existing unresolved closed issues
"""
import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_fix_existing_issue():
    """Test fixing an existing closed but unresolved issue"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    issue_key = input("Enter a closed but unresolved issue key to test: ").strip()
    
    if not issue_key:
        print("No issue key provided")
        return
    
    print(f"Testing resolution fix for: {issue_key}")
    print("=" * 50)
    
    try:
        # Check current status
        issue = jira.get_issue(issue_key)
        fields = issue.get("fields", {})
        current_status = fields.get("status", {}).get("name", "Unknown")
        current_resolution = fields.get("resolution")
        resolution_name = current_resolution.get("name") if current_resolution else "Unresolved"
        
        print(f"Current Status: {current_status}")
        print(f"Current Resolution: {resolution_name}")
        print()
        
        if resolution_name != "Unresolved":
            print(f"✓ Issue already has resolution: {resolution_name}")
            return
        
        # Try the new enhanced method
        print("Attempting to set resolution using enhanced method...")
        success = jira.transition_to_done_with_resolution(issue_key, "Done")
        
        if success:
            print("✓ Successfully applied resolution!")
            
            # Verify the change
            updated_issue = jira.get_issue(issue_key)
            updated_resolution = updated_issue.get("fields", {}).get("resolution")
            updated_resolution_name = updated_resolution.get("name") if updated_resolution else "Unresolved"
            
            print(f"✓ New resolution: {updated_resolution_name}")
        else:
            print("✗ Failed to set resolution using enhanced method")
            print("  This might be due to workflow restrictions")
            
            # Additional diagnostics
            print("\nDiagnostics:")
            print("-" * 20)
            
            # Check what transitions are available
            url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
            resp = jira.session.get(url)
            if resp.ok:
                transitions = resp.json().get("transitions", [])
                trans_names = [t.get("name", "Unknown") for t in transitions]
                print(f"Available transitions: {trans_names}")
                
                # Check if any transition has resolution
                has_resolution_trans = False
                for trans in transitions:
                    if "resolution" in trans.get("fields", {}):
                        has_resolution_trans = True
                        print(f"  → {trans.get('name')} supports resolution")
                
                if not has_resolution_trans:
                    print("  → No transitions support resolution setting")
            
            print("\nThis issue may require manual resolution in Jira UI")
            print("or the workflow may need to be configured differently.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Test Resolution Fix for Existing Issues")
    print("=" * 50)
    test_fix_existing_issue()