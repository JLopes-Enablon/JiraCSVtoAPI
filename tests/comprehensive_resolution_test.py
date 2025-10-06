#!/usr/bin/env python3
"""
Comprehensive API test to understand resolution workflow
Creates a single test issue and analyzes the complete workflow
"""
import os
import json
from dotenv import load_dotenv
from jiraapi import JiraAPI

def comprehensive_resolution_test():
    """Test the complete resolution workflow with API queries"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    if not all([jira_url, jira_email, jira_token]):
        print("Error: Missing environment variables")
        return
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("Comprehensive Resolution Workflow Test")
    print("=" * 60)
    
    # Test data from your CSV
    test_summary = "TEST - Resolution API Analysis (DELETE AFTER TESTING)"
    test_issue_type = "Story"
    
    print(f"Creating test {test_issue_type}: {test_summary}")
    
    try:
        # Step 1: Create the issue
        test_issue = jira.create_issue(
            project_key=project_id,
            summary=test_summary,
            issue_type=test_issue_type,
            assignee=None
        )
        
        issue_key = test_issue["key"]
        print(f"✓ Created test issue: {issue_key}")
        print()
        
        # Step 2: Get initial status and analyze workflow
        print("STEP 1: Analyzing initial workflow...")
        print("-" * 40)
        
        issue = jira.get_issue(issue_key)
        initial_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        print(f"Initial Status: {initial_status}")
        
        # Step 3: Get ALL available transitions with detailed analysis
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = jira.session.get(url)
        transitions_data = resp.json()
        transitions = transitions_data.get("transitions", [])
        
        print(f"Available transitions from '{initial_status}':")
        
        closing_transitions = []
        resolution_transitions = []
        
        for i, transition in enumerate(transitions, 1):
            trans_name = transition.get("name", "Unknown")
            trans_id = transition.get("id", "Unknown")
            to_status = transition.get("to", {}).get("name", "Unknown")
            trans_fields = transition.get("fields", {})
            
            print(f"\\n{i}. {trans_name} → {to_status} (ID: {trans_id})")
            
            # Check if this is a closing transition
            is_closing = any(keyword in to_status.lower() for keyword in 
                           ["done", "closed", "complete", "resolve", "finish"])
            
            if is_closing:
                closing_transitions.append(transition)
                print(f"   🎯 CLOSING TRANSITION")
            
            # Check available fields
            if trans_fields:
                print(f"   📝 Available fields: {list(trans_fields.keys())}")
                
                if "resolution" in trans_fields:
                    resolution_transitions.append(transition)
                    resolution_field = trans_fields["resolution"]
                    allowed_values = resolution_field.get("allowedValues", [])
                    required = resolution_field.get("required", False)
                    resolution_names = [r.get('name', 'Unknown') for r in allowed_values]
                    
                    print(f"   ✅ RESOLUTION FIELD AVAILABLE")
                    print(f"      Required: {required}")
                    print(f"      Options: {resolution_names}")
            else:
                print(f"   ❌ No editable fields")
        
        # Step 4: Analyze findings
        print("\\n" + "=" * 60)
        print("ANALYSIS RESULTS:")
        print("=" * 60)
        
        if closing_transitions:
            print(f"✓ Found {len(closing_transitions)} closing transition(s)")
            for trans in closing_transitions:
                print(f"  - {trans.get('name')} → {trans.get('to', {}).get('name')}")
        else:
            print("❌ No closing transitions found from initial status")
        
        if resolution_transitions:
            print(f"✓ Found {len(resolution_transitions)} transition(s) with resolution field")
            for trans in resolution_transitions:
                print(f"  - {trans.get('name')} → {trans.get('to', {}).get('name')}")
        else:
            print("❌ No transitions with resolution field found")
        
        # Find transitions that are BOTH closing AND have resolution
        closing_with_resolution = [t for t in transitions if 
                                 any(keyword in t.get('to', {}).get('name', '').lower() for keyword in 
                                     ["done", "closed", "complete", "resolve", "finish"]) and
                                 "resolution" in t.get("fields", {})]
        
        if closing_with_resolution:
            print(f"🎯 PERFECT: Found {len(closing_with_resolution)} transition(s) that close AND set resolution!")
            target_transition = closing_with_resolution[0]  # Use the first one
            
            print(f"\\nTesting transition: {target_transition.get('name')}")
            print("-" * 40)
            
            # Step 5: Test the transition with resolution
            trans_id = target_transition.get("id")
            resolution_field = target_transition.get("fields", {}).get("resolution", {})
            resolution_options = resolution_field.get("allowedValues", [])
            
            # Find "Done" resolution or use first available
            selected_resolution = None
            for res in resolution_options:
                if res.get("name", "").lower() == "done":
                    selected_resolution = {"id": res["id"]}
                    print(f"✓ Using 'Done' resolution (ID: {res['id']})")
                    break
            
            if not selected_resolution and resolution_options:
                first_res = resolution_options[0]
                selected_resolution = {"id": first_res["id"]}
                print(f"✓ Using first available resolution: {first_res.get('name')} (ID: {first_res['id']})")
            
            if selected_resolution:
                # Perform the transition with resolution
                transition_data = {
                    "transition": {"id": trans_id},
                    "fields": {"resolution": selected_resolution}
                }
                
                print(f"\\nExecuting transition with data: {json.dumps(transition_data, indent=2)}")
                
                post_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
                post_resp = jira.session.post(post_url, json=transition_data)
                
                if post_resp.ok:
                    print("✅ TRANSITION SUCCESSFUL!")
                    
                    # Verify the result
                    updated_issue = jira.get_issue(issue_key)
                    final_status = updated_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                    final_resolution = updated_issue.get("fields", {}).get("resolution")
                    final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                    
                    print(f"\\nFINAL RESULT:")
                    print(f"Status: {final_status}")
                    print(f"Resolution: {final_resolution_name}")
                    
                    if final_resolution_name != "Unresolved":
                        print("🎉 SUCCESS! Resolution was set correctly!")
                        return issue_key, True
                    else:
                        print("❌ FAILED: Still showing as Unresolved")
                        return issue_key, False
                else:
                    print(f"❌ TRANSITION FAILED: {post_resp.status_code} {post_resp.text}")
                    return issue_key, False
            else:
                print("❌ No resolution options available")
                return issue_key, False
        else:
            print("❌ PROBLEM: No transitions found that both close the issue AND set resolution")
            print("\\nThis means the Jira workflow may be configured to:")
            print("1. Require multiple steps (e.g., To Do → In Progress → Done)")
            print("2. Set resolution automatically without API control")
            print("3. Have resolution managed by workflow post-functions")
            
            # Test if we can get to closing states via intermediate transitions
            print("\\nSearching for multi-step workflow...")
            return issue_key, False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None, False

def cleanup_test_issue(issue_key):
    """Ask user what to do with the test issue"""
    if issue_key:
        print("\\n" + "=" * 60)
        print("CLEANUP")
        print("=" * 60)
        choice = input(f"Test issue {issue_key} was created. What would you like to do?\\n1. Leave it (delete manually from Jira)\\n2. Note it for reference\\nChoice [1]: ").strip()
        print(f"Test issue {issue_key} - Please delete manually from Jira UI when done testing")

if __name__ == "__main__":
    issue_key, success = comprehensive_resolution_test()
    
    print("\\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Found working solution for resolution setting!")
        print("The enhanced script should now work properly.")
    else:
        print("❌ Resolution setting issue persists")
        print("This indicates a Jira workflow configuration issue")
        print("that may require admin intervention or different approach.")
    
    cleanup_test_issue(issue_key)