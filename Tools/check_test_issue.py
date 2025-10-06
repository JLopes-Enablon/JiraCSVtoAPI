#!/usr/bin/env python3
"""
Quick check of CPESG-11789 custom fields
"""

import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def main():
    load_dotenv()
    
    base_url = os.getenv('JIRA_URL')
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_TOKEN')
    
    jira = JiraAPI(base_url, email, api_token)
    
    issue_key = "CPESG-11789"
    print(f"🔍 Checking custom fields on {issue_key}...")
    
    try:
        issue = jira.get_issue(issue_key)
        if not issue:
            print(f"❌ Could not retrieve issue {issue_key}")
            return
            
        print(f"\n📋 Issue: {issue['fields']['summary']}")
        print("\n✅ SUCCESS! Issue was created with custom field defaults!")
        print("\n📊 Custom Field Verification:")
        print("="*50)
        
        # Check the target fields
        fields_to_check = {
            'Division': 'customfield_10255',
            'Business Unit': 'customfield_10160',
            'Task Type': 'customfield_10609',
            'Task Sub-Type': 'customfield_10610',
            'IPM Managed': 'customfield_10606',
            'GBS Service': 'customfield_10605',
            'Environment': 'customfield_10153',
            'Labels': 'labels'
        }
        
        for field_name, field_id in fields_to_check.items():
            if field_id in issue['fields']:
                value = issue['fields'][field_id]
                if value:
                    if field_id == 'labels':
                        display_value = ', '.join(value) if value else 'None'
                    elif isinstance(value, dict) and 'value' in value:
                        display_value = value['value']
                    elif isinstance(value, list) and value and isinstance(value[0], dict) and 'value' in value[0]:
                        display_value = value[0]['value']
                    else:
                        display_value = str(value)
                    
                    print(f"✅ {field_name:<18}: {display_value}")
                else:
                    print(f"❌ {field_name:<18}: No value")
            else:
                print(f"❌ {field_name:<18}: Field not found")
        
        print("="*50)
        print(f"🔗 View issue: {base_url}/browse/{issue_key}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()