#!/usr/bin/env python3
"""
Check custom fields on CPESG-11786 to get the correct default values
"""

import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def check_issue_custom_fields():
    """Check custom fields on CPESG-11786"""
    
    load_dotenv()
    
    # Create Jira API instance
    jira = JiraAPI(
        base_url=os.getenv('JIRA_URL'),
        email=os.getenv('JIRA_EMAIL'),
        api_token=os.getenv('JIRA_TOKEN')
    )
    
    issue_key = "CPESG-11786"
    
    print(f"🔍 Checking custom fields on {issue_key}...\n")
    
    try:
        # Get issue details
        issue = jira.get_issue(issue_key)
        fields = issue.get("fields", {})
        
        # Fields we're interested in
        fields_to_check = {
            'Division': 'customfield_10255',
            'Business Unit': 'customfield_10160', 
            'Task Type': 'customfield_10609',
            'IPM Managed': 'customfield_10606',
            'Labels': 'labels'
        }
        
        print(f"📋 Custom fields on {issue_key}:")
        print(f"📌 Summary: {fields.get('summary', 'N/A')}")
        print()
        
        env_values = {}
        
        for field_name, field_id in fields_to_check.items():
            field_value = fields.get(field_id)
            
            if field_id == 'labels':
                if field_value:
                    labels_str = ','.join(field_value)
                    print(f"✅ {field_name}: {labels_str}")
                    env_values[f'FIELD_LABELS'] = labels_str
                else:
                    print(f"❌ {field_name}: Not set")
            else:
                if field_value:
                    value = field_value.get('value', 'N/A')
                    print(f"✅ {field_name}: {value}")
                    env_key = f"FIELD_{field_name.upper().replace(' ', '_')}"
                    env_values[env_key] = value
                else:
                    print(f"❌ {field_name}: Not set")
        
        print(f"\n🔧 Recommended .env values based on {issue_key}:")
        print("# Custom Field Defaults - Applied during issue creation")
        
        for env_key, value in env_values.items():
            print(f"{env_key}='{value}'")
        
        return env_values
        
    except Exception as e:
        print(f"❌ Error checking issue: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    check_issue_custom_fields()