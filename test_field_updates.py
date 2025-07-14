#!/usr/bin/env python3
"""
test_field_updates.py

Comprehensive test script to diagnose and fix Story Points and Original Estimate update issues.
This script will:
1. Validate field metadata from your Jira instance
2. Test different API approaches for updating these fields
3. Check field permissions and screen configurations
4. Provide corrected field mappings
"""

import os
import json
import requests
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

class JiraFieldTester:
    def __init__(self):
        self.base_url = os.getenv('JIRA_URL')
        self.email = os.getenv('JIRA_EMAIL')
        self.token = os.getenv('JIRA_TOKEN')
        
        if not all([self.base_url, self.email, self.token]):
            print("❌ Missing JIRA credentials in .env file")
            sys.exit(1)
            
        self.session = requests.Session()
        self.session.auth = (self.email, self.token)
        print(f"🔗 Connected to: {self.base_url}")
        print(f"👤 User: {self.email}")
        print()

    def get_all_fields(self):
        """Get all Jira fields and identify Story Points and time tracking fields"""
        print("🔍 Fetching all Jira fields...")
        url = f"{self.base_url}/rest/api/3/field"
        response = self.session.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch fields: {response.status_code} - {response.text}")
            return None
            
        fields = response.json()
        
        # Look for Story Points related fields
        story_point_fields = []
        time_fields = []
        
        for field in fields:
            field_name = field.get('name', '').lower()
            field_id = field.get('id', '')
            
            if 'story' in field_name and 'point' in field_name:
                story_point_fields.append({
                    'id': field_id,
                    'name': field.get('name'),
                    'custom': field.get('custom', False),
                    'schema': field.get('schema', {})
                })
            
            if any(word in field_name for word in ['time', 'estimate', 'tracking']):
                time_fields.append({
                    'id': field_id,
                    'name': field.get('name'),
                    'custom': field.get('custom', False),
                    'schema': field.get('schema', {})
                })
        
        print(f"📊 Found {len(story_point_fields)} Story Points related fields:")
        for field in story_point_fields:
            print(f"   • {field['id']}: {field['name']} (Custom: {field['custom']})")
            
        print(f"⏱️  Found {len(time_fields)} Time related fields:")
        for field in time_fields:
            print(f"   • {field['id']}: {field['name']} (Custom: {field['custom']})")
            
        print()
        return fields, story_point_fields, time_fields

    def get_issue_metadata(self, issue_key):
        """Get detailed metadata for a specific issue"""
        print(f"🎯 Analyzing issue: {issue_key}")
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch issue: {response.status_code} - {response.text}")
            return None
            
        issue = response.json()
        fields = issue.get('fields', {})
        
        print(f"   Issue Type: {fields.get('issuetype', {}).get('name', 'Unknown')}")
        print(f"   Status: {fields.get('status', {}).get('name', 'Unknown')}")
        print(f"   Project: {fields.get('project', {}).get('key', 'Unknown')}")
        
        # Check current Story Points value
        for field_id in ['customfield_10016', 'customfield_10146', 'customfield_10004']:
            if field_id in fields:
                value = fields.get(field_id)
                print(f"   Story Points ({field_id}): {value}")
                
        # Check timetracking
        timetracking = fields.get('timetracking', {})
        print(f"   Time Tracking: {timetracking}")
        
        print()
        return issue

    def get_issue_edit_metadata(self, issue_key):
        """Get edit metadata to see which fields can be updated"""
        print(f"✏️  Checking editable fields for: {issue_key}")
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/editmeta"
        response = self.session.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch edit metadata: {response.status_code} - {response.text}")
            return None
            
        metadata = response.json()
        editable_fields = metadata.get('fields', {})
        
        # Check for Story Points fields
        story_point_editable = []
        time_editable = []
        
        for field_id, field_info in editable_fields.items():
            field_name = field_info.get('name', '').lower()
            
            if 'story' in field_name and 'point' in field_name:
                story_point_editable.append({
                    'id': field_id,
                    'name': field_info.get('name'),
                    'required': field_info.get('required', False),
                    'schema': field_info.get('schema', {})
                })
                
            if field_id == 'timetracking' or 'time' in field_name or 'estimate' in field_name:
                time_editable.append({
                    'id': field_id,
                    'name': field_info.get('name'),
                    'required': field_info.get('required', False),
                    'schema': field_info.get('schema', {})
                })
        
        print(f"   ✅ Editable Story Points fields: {len(story_point_editable)}")
        for field in story_point_editable:
            print(f"      • {field['id']}: {field['name']} (Required: {field['required']})")
            
        print(f"   ✅ Editable Time fields: {len(time_editable)}")
        for field in time_editable:
            print(f"      • {field['id']}: {field['name']} (Required: {field['required']})")
        
        print()
        return editable_fields

    def test_story_points_update(self, issue_key, story_point_field_id, test_value=1):
        """Test updating Story Points with different approaches"""
        print(f"🧪 Testing Story Points update on {issue_key}")
        print(f"   Field ID: {story_point_field_id}")
        print(f"   Test Value: {test_value}")
        
        # Method 1: Direct field update
        print("   Method 1: Direct field update")
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        payload = {"fields": {story_point_field_id: test_value}}
        
        response = self.session.put(url, json=payload)
        print(f"      Status: {response.status_code}")
        if response.status_code != 204:
            print(f"      Error: {response.text}")
        else:
            print("      ✅ Success!")
            
        print()

    def test_time_tracking_update(self, issue_key, test_estimate="1h"):
        """Test updating Original Estimate with different approaches"""
        print(f"🧪 Testing Time Tracking update on {issue_key}")
        print(f"   Test Estimate: {test_estimate}")
        
        # Method 1: timetracking field
        print("   Method 1: timetracking field")
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        payload = {"fields": {"timetracking": {"originalEstimate": test_estimate}}}
        
        response = self.session.put(url, json=payload)
        print(f"      Status: {response.status_code}")
        if response.status_code != 204:
            print(f"      Error: {response.text}")
        else:
            print("      ✅ Success!")
            
        # Method 2: Just originalEstimate
        print("   Method 2: originalEstimate field directly")
        payload = {"fields": {"originalEstimate": test_estimate}}
        
        response = self.session.put(url, json=payload)
        print(f"      Status: {response.status_code}")
        if response.status_code != 204:
            print(f"      Error: {response.text}")
        else:
            print("      ✅ Success!")
            
        print()

    def get_project_issue_types(self, project_key):
        """Get all issue types for a project to understand screen configurations"""
        print(f"📋 Getting issue types for project: {project_key}")
        url = f"{self.base_url}/rest/api/3/project/{project_key}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch project: {response.status_code} - {response.text}")
            return None
            
        project = response.json()
        issue_types = project.get('issueTypes', [])
        
        print(f"   Found {len(issue_types)} issue types:")
        for issue_type in issue_types:
            print(f"      • {issue_type.get('name')} (ID: {issue_type.get('id')})")
            
        print()
        return issue_types

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_field_updates.py <ISSUE_KEY>")
        print("Example: python test_field_updates.py CPESG-3251")
        sys.exit(1)
        
    issue_key = sys.argv[1]
    
    print("🔧 Jira Field Update Diagnostic Tool")
    print("=" * 50)
    
    tester = JiraFieldTester()
    
    # Step 1: Get all fields
    all_fields, story_fields, time_fields = tester.get_all_fields()
    
    # Step 2: Analyze the specific issue
    issue = tester.get_issue_metadata(issue_key)
    if not issue:
        print("❌ Cannot continue without issue data")
        sys.exit(1)
    
    # Step 3: Check what fields can be edited
    editable_fields = tester.get_issue_edit_metadata(issue_key)
    if not editable_fields:
        print("❌ Cannot get editable fields")
        sys.exit(1)
    
    # Step 4: Get project info
    project_key = issue['fields']['project']['key']
    issue_types = tester.get_project_issue_types(project_key)
    
    # Step 5: Test actual updates if there are editable Story Points fields
    if story_fields:
        for field in story_fields:
            field_id = field['id']
            # Check if this field is editable
            if field_id in editable_fields:
                print(f"🎯 Found editable Story Points field: {field_id}")
                confirm = input(f"   Test updating {issue_key} with Story Points field {field_id}? (y/n): ")
                if confirm.lower() == 'y':
                    tester.test_story_points_update(issue_key, field_id, 1)
    
    # Step 6: Test time tracking if editable
    if 'timetracking' in editable_fields:
        print(f"🎯 Found editable timetracking field")
        confirm = input(f"   Test updating {issue_key} with Original Estimate? (y/n): ")
        if confirm.lower() == 'y':
            tester.test_time_tracking_update(issue_key, "30m")
    
    print("🏁 Diagnostic complete!")
    print("\n📝 RECOMMENDATIONS:")
    print("   1. Use only field IDs that appear in 'editable fields'")
    print("   2. Check Jira screen configurations for missing fields")
    print("   3. Verify field permissions for your user role")
    print("   4. Consider using different API endpoints if standard updates fail")

if __name__ == "__main__":
    main()
