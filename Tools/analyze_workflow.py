#!/usr/bin/env python3
"""
Comprehensive resolution strategy for Jira issues
"""
import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def analyze_issue_workflow(issue_key):
    """Analyze the complete workflow for an issue"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print(f"Complete Workflow Analysis for: {issue_key}")
    print("=" * 60)
    
    try:
        # 1. Get current issue details
        issue = jira.get_issue(issue_key)
        fields = issue.get("fields", {})
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")
        current_status = fields.get("status", {}).get("name", "Unknown")
        current_resolution = fields.get("resolution")
        resolution_name = current_resolution.get("name") if current_resolution else "Unresolved"
        
        print(f"Issue Type: {issue_type}")
        print(f"Current Status: {current_status}")
        print(f"Current Resolution: {resolution_name}")
        print()
        
        # 2. Get all available transitions
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = jira.session.get(url)
        if resp.ok:
            transitions_data = resp.json()
            transitions = transitions_data.get("transitions", [])
            
            print("All Available Transitions:")
            print("-" * 40)
            
            for i, transition in enumerate(transitions, 1):
                trans_name = transition.get("name", "Unknown")
                trans_id = transition.get("id", "Unknown")
                to_status = transition.get("to", {}).get("name", "Unknown")
                trans_fields = transition.get("fields", {})
                
                print(f"{i}. {trans_name} → {to_status} (ID: {trans_id})")
                
                # Check what fields are available in this transition
                if trans_fields:
                    print(f"   Available fields: {list(trans_fields.keys())}")
                    
                    # Check resolution specifically
                    if "resolution" in trans_fields:
                        resolution_field = trans_fields["resolution"]
                        allowed_values = resolution_field.get("allowedValues", [])
                        resolution_names = [r.get('name', 'Unknown') for r in allowed_values]
                        required = resolution_field.get("required", False)
                        print(f"   → Resolution options: {resolution_names}")
                        print(f"   → Resolution required: {required}")
                else:
                    print(f"   No editable fields in this transition")
                print()
        
        # 3. Check what would happen if we try different approaches
        print("Resolution Setting Analysis:")
        print("-" * 40)
        
        # Try approach 1: Direct resolution edit
        resolutions = jira.get_available_resolutions(issue_key)
        if resolutions:
            print("✓ Resolution field is directly editable")
            resolution_names = [r.get('name', 'Unknown') for r in resolutions]
            print(f"  Available: {resolution_names}")
        else:
            print("✗ Resolution field is not directly editable")
        
        # Try approach 2: Look for resolution in transitions
        transitions_with_resolution = []
        for transition in transitions:
            trans_fields = transition.get("fields", {})
            if "resolution" in trans_fields:
                transitions_with_resolution.append(transition.get("name", "Unknown"))
        
        if transitions_with_resolution:
            print(f"✓ Resolution can be set via transitions: {transitions_with_resolution}")
        else:
            print("✗ No transitions allow setting resolution")
            
        print()
        print("Recommendations:")
        print("-" * 40)
        
        if transitions_with_resolution:
            print("✓ Use transition-based resolution setting")
            print(f"  Recommended transitions: {transitions_with_resolution}")
        elif resolutions:
            print("✓ Use direct resolution field editing")
        else:
            print("⚠️  This issue type/status may not support resolution setting")
            print("   Consider checking Jira workflow configuration")
            print("   Or the issue may need to be in a different status first")
            
    except Exception as e:
        print(f"Error analyzing workflow: {e}")

if __name__ == "__main__":
    print("Jira Workflow and Resolution Analysis Tool")
    print("=" * 60)
    
    issue_key = input("Enter an issue key to analyze: ").strip()
    
    if issue_key:
        analyze_issue_workflow(issue_key)
    else:
        print("No issue key provided.")