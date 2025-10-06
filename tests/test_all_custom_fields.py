#!/usr/bin/env python3
"""
Test all 8 custom field defaults by creating a test issue
"""

import os
import sys
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_all_custom_field_defaults():
    try:
        load_dotenv()
        
        # Initialize Jira API
        base_url = os.getenv('JIRA_URL')
        email = os.getenv('JIRA_EMAIL')
        api_token = os.getenv('JIRA_TOKEN')
        project_id = os.getenv('JIRA_PROJECT_ID', 'PROJ')
        
        jira = JiraAPI(base_url, email, api_token)
        
        print("🧪 Testing Custom Field Defaults - Creating Test Issue...")
        print("="*70)
        
        # Create test issue
        test_summary = "TEST - Custom Field Defaults Verification (DELETE AFTER)"
        test_description = "TEST ISSUE - DELETE AFTER VERIFICATION. This issue was created to verify that all 8 custom field defaults are being applied correctly."
        
        # Create the issue (this should apply all custom field defaults automatically)
        issue_key = jira.create_issue(
            project_key=project_id,
            summary=test_summary,
            issue_type="Story"
        )
        
        if issue_key:
            print(f"✅ Test issue created: {issue_key}")
            
            # Now verify the fields were set correctly
            print(f"\n🔍 Verifying custom fields on {issue_key}...")
            
            issue = jira.get_issue(issue_key)
            if issue:
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
                
                print("\n📋 Field Verification Results:")
                print("-" * 50)
                
                all_correct = True
                for field_name, field_id in fields_to_check.items():
                    if field_id in issue['fields']:
                        value = issue['fields'][field_id]
                        
                        if field_id == 'labels':
                            display_value = ', '.join(value) if value else 'None'
                            expected = 'Enablon'
                            is_correct = 'Enablon' in (value or [])
                        elif isinstance(value, dict) and 'value' in value:
                            display_value = value['value']
                            expected_values = {
                                'customfield_10255': 'CP&ESG',
                                'customfield_10160': 'PROJ-Enablon',
                                'customfield_10609': 'General',
                                'customfield_10610': 'Managed Work',
                                'customfield_10606': 'Yes',
                                'customfield_10605': 'Yes',
                                'customfield_10153': 'Cloud'
                            }
                            expected = expected_values.get(field_id, 'Unknown')
                            is_correct = display_value == expected
                        else:
                            display_value = str(value) if value else 'None'
                            is_correct = False
                        
                        status = "✅" if is_correct else "❌"
                        print(f"{status} {field_name:<18}: {display_value}")
                        
                        if not is_correct:
                            all_correct = False
                    else:
                        print(f"❌ {field_name:<18}: Field not found")
                        all_correct = False
                
                print("-" * 50)
                if all_correct:
                    print("🎉 SUCCESS: All custom field defaults applied correctly!")
                    print(f"🔗 View issue: {base_url}/browse/{issue_key}")
                else:
                    print("⚠️  Some fields were not set correctly. Check configuration.")
                    
                return issue_key, all_correct
            else:
                print(f"❌ Could not retrieve created issue {issue_key}")
                return issue_key, False
        else:
            print("❌ Failed to create test issue")
            return None, False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None, False

if __name__ == "__main__":
    test_all_custom_field_defaults()