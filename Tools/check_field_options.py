#!/usr/bin/env python3
"""
Check available options for custom dropdown fields
"""

import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def check_field_options():
    """Check available options for custom dropdown fields"""
    
    load_dotenv()
    
    # Create Jira API instance
    jira = JiraAPI(
        base_url=os.getenv('JIRA_URL'),
        email=os.getenv('JIRA_EMAIL'),
        api_token=os.getenv('JIRA_TOKEN')
    )
    
    # Fields to check
    fields_to_check = {
        'Division': 'customfield_10255',
        'Business Unit': 'customfield_10160', 
        'Task Type': 'customfield_10609',
        'IPM Managed': 'customfield_10606'
    }
    
    print("🔍 Checking available options for custom dropdown fields...\n")
    
    for field_name, field_id in fields_to_check.items():
        print(f"📋 {field_name} ({field_id}):")
        
        try:
            # Get create metadata for the project to see available options
            url = f"{jira.base_url}/rest/api/3/issue/createmeta"
            params = {
                'projectKeys': 'CPESG',
                'issuetypeNames': 'Story',
                'expand': 'projects.issuetypes.fields'
            }
            
            response = jira.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Find the field in the response
            projects = data.get('projects', [])
            if projects:
                issue_types = projects[0].get('issuetypes', [])
                if issue_types:
                    fields = issue_types[0].get('fields', {})
                    field_data = fields.get(field_id)
                    
                    if field_data:
                        allowed_values = field_data.get('allowedValues', [])
                        if allowed_values:
                            print(f"   Available options:")
                            for option in allowed_values:
                                value = option.get('value', option.get('name', 'N/A'))
                                option_id = option.get('id', 'N/A')
                                print(f"   • '{value}' (ID: {option_id})")
                        else:
                            print(f"   ⚠️  No allowed values found (field may be text input)")
                    else:
                        print(f"   ❌ Field not found in create metadata")
                else:
                    print(f"   ❌ No issue types found")
            else:
                print(f"   ❌ No projects found")
                
        except Exception as e:
            print(f"   ❌ Error checking field: {e}")
        
        print()

if __name__ == "__main__":
    check_field_options()