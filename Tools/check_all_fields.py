#!/usr/bin/env python3
"""
Comprehensive field checker for PROJ-11786
Maps field names to their IDs and values
"""

import os
import sys
from jiraapi import JiraAPI

def check_all_custom_fields():
    try:
        # Initialize Jira API with environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        base_url = os.getenv('JIRA_URL')
        email = os.getenv('JIRA_EMAIL')
        api_token = os.getenv('JIRA_TOKEN')
        
        if not all([base_url, email, api_token]):
            print("❌ Missing Jira credentials in .env file")
            return None
            
        jira = JiraAPI(base_url, email, api_token)
        
        issue_key = "PROJ-11786"
        print(f"🔍 Checking ALL fields on {issue_key}...")
        
        # Get the issue
        issue = jira.get_issue(issue_key)
        if not issue:
            print(f"❌ Could not retrieve issue {issue_key}")
            return
            
        print(f"\n📋 Issue: {issue['fields']['summary']}")
        print("\n" + "="*80)
        print("FIELD ANALYSIS - Field Name: Field ID: Current Value")
        print("="*80)
        
        # Target fields from user's list
        target_fields = {
            'Labels': 'labels',
            'Environment': None,
            'Barometer ID': None, 
            'Clarizen ID': None,
            'Rainier ID': None,
            'GBS Service': None,
            'IPM Managed': 'customfield_10606',
            'Task Sub-Status': None,
            'Task Type': 'customfield_10609',
            'Task Sub-Type': None,
            'Division': 'customfield_10255',
            'Business Unit': 'customfield_10160'
        }
        
        # Check all fields in the issue
        found_fields = {}
        
        # Check known fields first
        for field_name, known_id in target_fields.items():
            if known_id:
                if known_id in issue['fields']:
                    value = issue['fields'][known_id]
                    if value:
                        if known_id == 'labels':
                            display_value = ', '.join(value) if value else 'None'
                        elif isinstance(value, dict) and 'value' in value:
                            display_value = value['value']
                        elif isinstance(value, list) and value and isinstance(value[0], dict) and 'value' in value[0]:
                            display_value = value[0]['value']
                        else:
                            display_value = str(value)
                        
                        found_fields[field_name] = {
                            'id': known_id,
                            'value': display_value
                        }
                        print(f"✅ {field_name:<20}: {known_id:<20}: {display_value}")
        
        # Now search for unknown fields by looking through all custom fields
        print(f"\n🔍 Searching for unknown fields...")
        
        for field_id, field_value in issue['fields'].items():
            if field_id.startswith('customfield_') and field_value:
                # Check if this field might match our target fields
                if isinstance(field_value, dict) and 'value' in field_value:
                    value_str = field_value['value']
                elif isinstance(field_value, list) and field_value:
                    if isinstance(field_value[0], dict) and 'value' in field_value[0]:
                        value_str = field_value[0]['value']
                    else:
                        value_str = str(field_value[0])
                else:
                    value_str = str(field_value)
                
                # Check if this matches any of our target values
                if value_str in ['Cloud', 'Yes', 'Managed Work']:
                    print(f"🆔 FOUND: {field_id:<20}: {value_str}")
                    
                    # Try to guess the field name
                    if value_str == 'Cloud':
                        found_fields['Environment'] = {'id': field_id, 'value': value_str}
                    elif value_str == 'Yes' and field_id != 'customfield_10606':  # Not IPM Managed
                        found_fields['GBS Service'] = {'id': field_id, 'value': value_str}
                    elif value_str == 'Managed Work':
                        found_fields['Task Sub-Type'] = {'id': field_id, 'value': value_str}
        
        # Generate .env configuration
        print(f"\n" + "="*80)
        print("RECOMMENDED .ENV CONFIGURATION")
        print("="*80)
        
        for field_name, field_data in found_fields.items():
            env_name = field_name.upper().replace(' ', '_').replace('-', '_')
            print(f"FIELD_{env_name}='{field_data['value']}'")
        
        return found_fields
        
    except Exception as e:
        print(f"❌ Error checking fields: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_all_custom_fields()