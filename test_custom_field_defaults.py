#!/usr/bin/env python3
"""
Test custom field defaults functionality
Creates a test issue to verify .env custom field defaults are applied
"""

import os
import sys
from jiraapi import JiraAPI, load_custom_field_defaults

def test_custom_field_defaults():
    """Test that custom field defaults are loaded and applied correctly"""
    
    print("🧪 Testing Custom Field Defaults Functionality\n")
    
    # Test 1: Load custom field defaults
    print("1️⃣ Testing custom field defaults loading...")
    try:
        defaults = load_custom_field_defaults()
        print(f"✅ Successfully loaded {len(defaults)} custom field defaults:")
        for field_id, value in defaults.items():
            print(f"   - {field_id}: {value}")
    except Exception as e:
        print(f"❌ Failed to load defaults: {e}")
        return False
    
    print("\n2️⃣ Testing issue creation with custom defaults...")
    
    # Load environment variables for Jira API
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create Jira API instance
    jira = JiraAPI(
        base_url=os.getenv('JIRA_URL'),
        email=os.getenv('JIRA_EMAIL'),
        api_token=os.getenv('JIRA_TOKEN')
    )
    
    try:
        # Create a test issue (custom defaults should be applied automatically)
        test_issue = jira.create_issue(
            project_key="CPESG",
            summary="TEST - Custom Field Defaults (DELETE AFTER)",
            issue_type="Story"
        )
        
        issue_key = test_issue.get("key")
        print(f"✅ Successfully created test issue: {issue_key}")
        
        # Verify the issue was created with defaults
        issue_details = jira.get_issue(issue_key)
        print(f"✅ Retrieved issue details for verification")
        
        # Check some of the custom fields
        fields = issue_details.get("fields", {})
        
        print("\n📋 Verifying applied custom fields:")
        
        # Division
        division = fields.get("customfield_10255")
        if division:
            print(f"   ✅ Division: {division.get('value', 'N/A')}")
        else:
            print(f"   ⚠️  Division: Not set")
        
        # Business Unit  
        business_unit = fields.get("customfield_10160")
        if business_unit:
            print(f"   ✅ Business Unit: {business_unit.get('value', 'N/A')}")
        else:
            print(f"   ⚠️  Business Unit: Not set")
        
        # Task Type
        task_type = fields.get("customfield_10609")
        if task_type:
            print(f"   ✅ Task Type: {task_type.get('value', 'N/A')}")
        else:
            print(f"   ⚠️  Task Type: Not set")
        
        # IPM Managed
        ipm_managed = fields.get("customfield_10606")
        if ipm_managed:
            print(f"   ✅ IPM Managed: {ipm_managed.get('value', 'N/A')}")
        else:
            print(f"   ⚠️  IPM Managed: Not set")
        
        # Labels
        labels = fields.get("labels", [])
        if labels:
            print(f"   ✅ Labels: {', '.join(labels)}")
        else:
            print(f"   ⚠️  Labels: Not set")
        
        print(f"\n🎉 TEST COMPLETED - Issue {issue_key} created with custom defaults")
        print(f"👉 You can view it at: https://wkenterprise.atlassian.net/browse/{issue_key}")
        print(f"🗑️  Remember to delete this test issue when done")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_custom_field_defaults()
    sys.exit(0 if success else 1)