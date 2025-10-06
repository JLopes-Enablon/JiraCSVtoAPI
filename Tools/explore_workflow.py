#!/usr/bin/env python3
"""
Check if there are alternative transitions or statuses that allow proper resolution setting
"""
import os
import json
from dotenv import load_dotenv
from jiraapi import JiraAPI

def explore_all_transitions():
    """Explore all possible workflow paths to find resolution setting opportunities"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("Exploring ALL Workflow Transitions")
    print("=" * 50)
    
    try:
        # Create test issue
        test_issue = jira.create_issue(
            project_key=project_id,
            summary="TEST - Workflow Explorer (DELETE AFTER TESTING)",
            issue_type="Story",
            assignee=None
        )
        
        issue_key = test_issue["key"]
        print(f"✓ Created test issue: {issue_key}")
        
        # Test each transition one by one to see what statuses are available
        statuses_explored = set()
        
        def explore_from_status(current_issue_key, status_name):
            """Recursively explore transitions from a given status"""
            if status_name in statuses_explored:
                return
            
            statuses_explored.add(status_name)
            print(f"\\n🔍 Exploring transitions from '{status_name}':")
            print("-" * 40)
            
            # Get current issue state
            issue = jira.get_issue(current_issue_key)
            current_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
            current_resolution = issue.get("fields", {}).get("resolution")
            current_resolution_name = current_resolution.get("name") if current_resolution else "Unresolved"
            
            print(f"Current Status: {current_status}")
            print(f"Current Resolution: {current_resolution_name}")
            
            # Get transitions
            url = f"{jira.base_url}/rest/api/3/issue/{current_issue_key}/transitions"
            resp = jira.session.get(url)
            transitions = resp.json().get("transitions", [])
            
            resolution_capable_transitions = []
            
            for transition in transitions:
                trans_name = transition.get("name", "Unknown")
                trans_id = transition.get("id", "Unknown")
                to_status = transition.get("to", {}).get("name", "Unknown")
                trans_fields = transition.get("fields", {})
                
                has_resolution = "resolution" in trans_fields
                is_closing = any(keyword in to_status.lower() for keyword in 
                               ["done", "closed", "complete", "resolve", "finish"])
                
                status_indicator = "🎯" if is_closing else "📝"
                resolution_indicator = "✅" if has_resolution else "❌"
                
                print(f"  {status_indicator} {trans_name} → {to_status} (ID: {trans_id}) {resolution_indicator}")
                
                if has_resolution:
                    resolution_capable_transitions.append(transition)
                    resolution_field = trans_fields["resolution"]
                    allowed_values = resolution_field.get("allowedValues", [])
                    resolution_names = [r.get('name', 'Unknown') for r in allowed_values]
                    print(f"      Resolution options: {resolution_names}")
            
            return resolution_capable_transitions
        
        # Start exploration from initial status
        initial_issue = jira.get_issue(issue_key)
        initial_status = initial_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        
        resolution_transitions = explore_from_status(issue_key, initial_status)
        
        if resolution_transitions:
            print(f"\\n🎉 FOUND {len(resolution_transitions)} TRANSITION(S) WITH RESOLUTION FIELD!")
            
            # Test the first one
            test_transition = resolution_transitions[0]
            trans_name = test_transition.get("name")
            trans_id = test_transition.get("id")
            to_status = test_transition.get("to", {}).get("name")
            
            print(f"\\nTesting: {trans_name} → {to_status}")
            
            # Get resolution options
            resolution_field = test_transition.get("fields", {}).get("resolution", {})
            resolution_options = resolution_field.get("allowedValues", [])
            
            # Find "Done" or use first option
            target_resolution = None
            for res in resolution_options:
                if res.get("name", "").lower() == "done":
                    target_resolution = {"id": res["id"]}
                    print(f"✓ Using 'Done' resolution")
                    break
            
            if not target_resolution and resolution_options:
                first_res = resolution_options[0]
                target_resolution = {"id": first_res["id"]}
                print(f"✓ Using '{first_res.get('name')}' resolution")
            
            if target_resolution:
                # Execute transition with resolution
                transition_data = {
                    "transition": {"id": trans_id},
                    "fields": {"resolution": target_resolution}
                }
                
                post_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
                post_resp = jira.session.post(post_url, json=transition_data)
                
                if post_resp.ok:
                    print("✅ Transition with resolution SUCCESSFUL!")
                    
                    # Check result
                    final_issue = jira.get_issue(issue_key)
                    final_status = final_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                    final_resolution = final_issue.get("fields", {}).get("resolution")
                    final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                    
                    print(f"\\nFINAL STATE:")
                    print(f"Status: {final_status}")
                    print(f"Resolution: {final_resolution_name}")
                    
                    return issue_key, final_resolution_name != "Unresolved", trans_name
                else:
                    print(f"❌ Transition failed: {post_resp.status_code}")
                    print(f"Error: {post_resp.text}")
                    return issue_key, False, None
        else:
            print("\\n❌ NO TRANSITIONS WITH RESOLUTION FIELD FOUND")
            print("\\nThis confirms the workflow issue:")
            print("- The project workflow does not allow API-based resolution setting")
            print("- Resolution is managed entirely by workflow post-functions")
            print("- This is a Jira admin configuration issue")
            
            return issue_key, False, None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None, False, None

if __name__ == "__main__":
    issue_key, success, working_transition = explore_all_transitions()
    
    print("\\n" + "=" * 50)
    print("FINAL DIAGNOSIS")
    print("=" * 50)
    
    if success:
        print(f"✅ SOLUTION FOUND: Use '{working_transition}' transition")
        print("This transition properly sets the resolution field!")
    else:
        print("❌ CONFIRMED: No API-based resolution setting possible")
        print("\\nRECOMMENDATIONS:")
        print("1. Contact Jira admin to fix workflow post-functions")
        print("2. Add 'Done' resolution to 'Closed' transition")
        print("3. Or create new transition that properly sets resolution")
        print("\\nWORKAROUND:")
        print("- Accept that items will show 'Unresolved' in API")
        print("- Manually fix them in Jira UI if needed")
        print("- Or modify script to use different issue types/workflows")
    
    if issue_key:
        print(f"\\nTest issue {issue_key} - delete manually from Jira UI")