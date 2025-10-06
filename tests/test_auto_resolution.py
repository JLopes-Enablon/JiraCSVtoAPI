#!/usr/bin/env python3
"""
Test the automatic resolution setting when using the Closed transition
"""
import os
import json
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_automatic_resolution():
    """Test what happens when we use the Closed transition"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "CPESG")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("Testing Automatic Resolution Setting")
    print("=" * 50)
    
    # Test data
    test_summary = "TEST - Auto Resolution Check (DELETE AFTER TESTING)"
    
    try:
        # Create test issue
        test_issue = jira.create_issue(
            project_key=project_id,
            summary=test_summary,
            issue_type="Story",
            assignee=None
        )
        
        issue_key = test_issue["key"]
        print(f"✓ Created test issue: {issue_key}")
        
        # Get initial state
        issue = jira.get_issue(issue_key)
        initial_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        initial_resolution = issue.get("fields", {}).get("resolution")
        initial_resolution_name = initial_resolution.get("name") if initial_resolution else "Unresolved"
        
        print(f"Initial Status: {initial_status}")
        print(f"Initial Resolution: {initial_resolution_name}")
        
        # Perform the Closed transition (ID: 51)
        print("\\nExecuting 'Closed' transition...")
        transition_data = {"transition": {"id": "51"}}
        
        post_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        post_resp = jira.session.post(post_url, json=transition_data)
        
        if post_resp.ok:
            print("✅ Transition executed successfully")
            
            # Check final state
            updated_issue = jira.get_issue(issue_key)
            final_status = updated_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
            final_resolution = updated_issue.get("fields", {}).get("resolution")
            final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
            
            print(f"\\nFINAL RESULT:")
            print(f"Status: {final_status}")
            print(f"Resolution: {final_resolution_name}")
            
            if final_resolution_name == "Unresolved":
                print("\\n❌ CONFIRMED: The workflow sets resolution to 'Unresolved'")
                print("This is the root cause of your issue!")
                
                # Try to manually set resolution after transition
                print("\\nTesting manual resolution update after transition...")
                
                # Get available resolutions for the project
                project_url = f"{jira.base_url}/rest/api/3/project/{project_id}"
                project_resp = jira.session.get(project_url)
                
                if project_resp.ok:
                    # Try to update resolution directly
                    update_data = {
                        "fields": {
                            "resolution": {"name": "Done"}
                        }
                    }
                    
                    update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                    update_resp = jira.session.put(update_url, json=update_data)
                    
                    if update_resp.ok:
                        print("✅ Manual resolution update successful!")
                        
                        # Verify
                        final_check = jira.get_issue(issue_key)
                        final_res = final_check.get("fields", {}).get("resolution")
                        final_res_name = final_res.get("name") if final_res else "Unresolved"
                        print(f"Updated Resolution: {final_res_name}")
                        
                        if final_res_name == "Done":
                            print("🎉 SUCCESS! Manual resolution update works!")
                            return issue_key, "manual_update"
                        else:
                            print("❌ Manual update failed to stick")
                            return issue_key, "failed"
                    else:
                        print(f"❌ Manual resolution update failed: {update_resp.status_code}")
                        print(f"Error: {update_resp.text}")
                        return issue_key, "update_blocked"
                else:
                    print("❌ Could not get project info")
                    return issue_key, "no_project_info"
            else:
                print(f"✅ Workflow automatically set resolution to: {final_resolution_name}")
                return issue_key, "auto_resolution"
                
        else:
            print(f"❌ Transition failed: {post_resp.status_code}")
            print(f"Error: {post_resp.text}")
            return issue_key, "transition_failed"
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None, "error"

if __name__ == "__main__":
    issue_key, result = test_automatic_resolution()
    
    print("\\n" + "=" * 50)
    print("DIAGNOSIS COMPLETE")
    print("=" * 50)
    
    if result == "manual_update":
        print("✅ SOLUTION FOUND:")
        print("1. Use transition to close the issue")
        print("2. Immediately update resolution field separately")
        print("\\nThis can be implemented in your script!")
    elif result == "auto_resolution":
        print("✅ Workflow sets resolution automatically")
        print("The issue may be in your script's timing or check logic")
    elif result == "update_blocked":
        print("❌ Workflow prevents manual resolution updates")
        print("This requires Jira admin intervention to fix workflow")
    else:
        print(f"❌ Test result: {result}")
        print("Further investigation needed")
    
    if issue_key:
        print(f"\\nTest issue {issue_key} created - delete from Jira UI when done")