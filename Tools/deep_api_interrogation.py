#!/usr/bin/env python3
"""
Deep API interrogation to find exactly how resolution setting works
Since manual UI closing allows resolution setting, the API must support it somewhere
"""
import os
import json
from dotenv import load_dotenv
from jiraapi import JiraAPI

def deep_resolution_analysis():
    """Comprehensive analysis of resolution setting capabilities"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("DEEP API RESOLUTION ANALYSIS")
    print("=" * 60)
    
    try:
        # Create test issue
        test_issue = jira.create_issue(
            project_key=project_id,
            summary="DEEP TEST - Resolution Analysis (DELETE AFTER TESTING)",
            issue_type="Story",
            assignee=None
        )
        
        issue_key = test_issue["key"]
        print(f"✓ Created test issue: {issue_key}")
        
        # STEP 1: Get detailed transition information with expand parameters
        print("\nSTEP 1: Getting detailed transition data...")
        print("-" * 50)
        
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        
        # Try with different expand parameters to get all available data
        expand_options = [
            "",
            "transitions.fields",
            "transitions.fields.allowedValues", 
            "transitions.fields.schema",
            "fields",
            "transitions.fields,transitions.fields.allowedValues"
        ]
        
        best_transitions_data = None
        
        for expand in expand_options:
            params = {"expand": expand} if expand else {}
            resp = jira.session.get(url, params=params)
            
            if resp.ok:
                data = resp.json()
                transitions = data.get("transitions", [])
                
                print(f"\\nExpand: '{expand}' - Found {len(transitions)} transitions")
                
                # Check if any transitions have resolution field with this expand
                has_resolution = any("resolution" in t.get("fields", {}) for t in transitions)
                if has_resolution:
                    print(f"  ✅ HAS RESOLUTION FIELD!")
                    best_transitions_data = data
                    
                # Show detailed field info for "Closed" transition
                closed_transition = next((t for t in transitions if t.get("name") == "Closed"), None)
                if closed_transition:
                    fields = closed_transition.get("fields", {})
                    print(f"  Closed transition fields: {list(fields.keys())}")
                    
                    if "resolution" in fields:
                        resolution_field = fields["resolution"]
                        print(f"    Resolution field details: {json.dumps(resolution_field, indent=4)}")
        
        # STEP 2: Test the edit metadata for closed issues
        print("\n\nSTEP 2: Testing edit metadata...")
        print("-" * 50)
        
        # Check what fields are editable before transition
        editmeta_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/editmeta"
        editmeta_resp = jira.session.get(editmeta_url)
        
        if editmeta_resp.ok:
            editmeta = editmeta_resp.json()
            editable_fields = editmeta.get("fields", {}).keys()
            print(f"Fields editable in current state: {list(editable_fields)}")
            
            if "resolution" in editable_fields:
                print("✅ Resolution is editable in current state!")
                resolution_meta = editmeta["fields"]["resolution"]
                print(f"Resolution metadata: {json.dumps(resolution_meta, indent=2)}")
        
        # STEP 3: Get project resolutions
        print("\n\nSTEP 3: Getting project resolutions...")
        print("-" * 50)
        
        # Get all available resolutions for the project
        resolutions_url = f"{jira.base_url}/rest/api/3/resolution"
        resolutions_resp = jira.session.get(resolutions_url)
        
        if resolutions_resp.ok:
            resolutions = resolutions_resp.json()
            print("Available resolutions:")
            for res in resolutions:
                print(f"  - {res.get('name')} (ID: {res.get('id')})")
        
        # STEP 4: Try transition with explicit resolution using best data
        print("\n\nSTEP 4: Testing transition with resolution...")
        print("-" * 50)
        
        if best_transitions_data:
            transitions = best_transitions_data.get("transitions", [])
            closed_transition = next((t for t in transitions if t.get("name") == "Closed"), None)
            
            if closed_transition and "resolution" in closed_transition.get("fields", {}):
                print("Found Closed transition with resolution field!")
                
                resolution_field = closed_transition["fields"]["resolution"]
                allowed_values = resolution_field.get("allowedValues", [])
                
                print(f"Allowed resolution values for Closed transition:")
                for val in allowed_values:
                    print(f"  - {val.get('name')} (ID: {val.get('id')})")
                
                # Try to use "Done" resolution
                done_resolution = next((r for r in allowed_values if r.get("name") == "Done"), None)
                if not done_resolution and allowed_values:
                    done_resolution = allowed_values[0]  # Use first available
                
                if done_resolution:
                    print(f"\\nTesting transition with resolution: {done_resolution.get('name')}")
                    
                    transition_data = {
                        "transition": {"id": closed_transition["id"]},
                        "fields": {
                            "resolution": {"id": done_resolution["id"]}
                        }
                    }
                    
                    print(f"Transition payload: {json.dumps(transition_data, indent=2)}")
                    
                    post_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
                    post_resp = jira.session.post(post_url, json=transition_data)
                    
                    if post_resp.ok:
                        print("✅ TRANSITION WITH RESOLUTION SUCCESSFUL!")
                        
                        # Verify result
                        final_issue = jira.get_issue(issue_key)
                        final_status = final_issue.get("fields", {}).get("status", {}).get("name")
                        final_resolution = final_issue.get("fields", {}).get("resolution")
                        final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                        
                        print(f"\\nFINAL RESULT:")
                        print(f"Status: {final_status}")
                        print(f"Resolution: {final_resolution_name}")
                        
                        return issue_key, True, transition_data
                    else:
                        print(f"❌ Transition failed: {post_resp.status_code}")
                        print(f"Error details: {post_resp.text}")
                        
                        # Try to understand the error
                        try:
                            error_data = post_resp.json()
                            print(f"Error JSON: {json.dumps(error_data, indent=2)}")
                        except:
                            pass
                        
                        return issue_key, False, None
            else:
                print("❌ Closed transition still doesn't show resolution field even with expanded data")
        
        # STEP 5: Try alternative approach - transition first, then update
        print("\n\nSTEP 5: Alternative approach - transition then update...")
        print("-" * 50)
        
        # If we haven't transitioned yet, do basic transition first
        if best_transitions_data:
            current_issue = jira.get_issue(issue_key)
            current_status = current_issue.get("fields", {}).get("status", {}).get("name")
            
            if current_status != "Closed":
                print("Performing basic transition to Closed first...")
                
                basic_transition_data = {"transition": {"id": "51"}}  # Closed transition ID
                post_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
                basic_resp = jira.session.post(post_url, json=basic_transition_data)
                
                if basic_resp.ok:
                    print("✅ Basic transition successful")
                    
                    # Now try to update resolution
                    print("Attempting to update resolution after transition...")
                    
                    # Check editmeta for closed issue
                    closed_editmeta_resp = jira.session.get(editmeta_url)
                    if closed_editmeta_resp.ok:
                        closed_editmeta = closed_editmeta_resp.json()
                        closed_editable = closed_editmeta.get("fields", {}).keys()
                        print(f"Fields editable when closed: {list(closed_editable)}")
                        
                        if "resolution" in closed_editable:
                            print("✅ Resolution is editable when closed!")
                            
                            # Try to update resolution
                            if resolutions_resp.ok:
                                all_resolutions = resolutions_resp.json()
                                done_res = next((r for r in all_resolutions if r.get("name") == "Done"), None)
                                
                                if done_res:
                                    update_data = {
                                        "fields": {
                                            "resolution": {"id": done_res["id"]}
                                        }
                                    }
                                    
                                    update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                                    update_resp = jira.session.put(update_url, json=update_data)
                                    
                                    if update_resp.ok:
                                        print("✅ RESOLUTION UPDATE SUCCESSFUL!")
                                        
                                        # Final verification
                                        final_issue = jira.get_issue(issue_key)
                                        final_resolution = final_issue.get("fields", {}).get("resolution")
                                        final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                                        
                                        print(f"Final resolution: {final_resolution_name}")
                                        return issue_key, True, update_data
                                    else:
                                        print(f"❌ Resolution update failed: {update_resp.status_code}")
                                        print(f"Error: {update_resp.text}")
                        else:
                            print("❌ Resolution not editable when closed")
                else:
                    print(f"❌ Basic transition failed: {basic_resp.status_code}")
        
        return issue_key, False, None
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, False, None

if __name__ == "__main__":
    issue_key, success, working_payload = deep_resolution_analysis()
    
    print("\n" + "=" * 60)
    print("DEEP ANALYSIS COMPLETE")
    print("=" * 60)
    
    if success:
        print("🎉 FOUND WORKING SOLUTION!")
        print(f"Working payload: {json.dumps(working_payload, indent=2)}")
        print("\\nThis can be implemented in your main script!")
    else:
        print("❌ Still unable to set resolution via API")
        print("\\nPossible reasons:")
        print("1. Workflow configuration prevents API access")
        print("2. Special permissions required")
        print("3. UI uses different API endpoints")
        print("4. Field configuration issue")
    
    if issue_key:
        print(f"\\nTest issue {issue_key} - delete manually from Jira UI")