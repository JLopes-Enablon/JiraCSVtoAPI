#!/bin/bash
# Auto-activate venv and run with venv python
VENV="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV" ]; then
  source "$VENV"
fi
exec python "$0" "$@"
"""
fix_field_updates.py

Corrected field update methods for Story Points and Original Estimate based on diagnostic results.
This script provides the corrected implementations for your jiraapi.py
"""

import os
import json
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

def convert_time_to_seconds(time_str):
    """Convert time string like '1h 30m' to seconds"""
    if not time_str:
        return None
        
    time_str = str(time_str).strip()
    if not time_str:
        return None
    
    # Handle formats like "1h 30m", "2h", "45m"
    total_seconds = 0
    
    # Extract hours
    hour_match = re.search(r'(\d+)h', time_str)
    if hour_match:
        total_seconds += int(hour_match.group(1)) * 3600
    
    # Extract minutes
# Corrected field update methods for Story Points and Original Estimate based on diagnostic results.
# This script provides the corrected implementations for your jiraapi.py

# Load environment variables
load_dotenv()
    minute_match = re.search(r'(\d+)m', time_str)
    if minute_match:
        total_seconds += int(minute_match.group(1)) * 60
    
    return total_seconds if total_seconds > 0 else None

def get_issue_editable_fields(base_url, session, issue_key):
    """Get editable fields for a specific issue"""
    url = f"{base_url}/rest/api/3/issue/{issue_key}/editmeta"
    response = session.get(url)
    if response.status_code == 200:
        return response.json().get('fields', {})
    return {}

def update_story_points_corrected(base_url, session, issue_key, story_points_value, logger=None):
    """
"""
fix_field_updates.py

Usage: Run directly to apply field fixes as needed.
"""
    Corrected Story Points update using the proper field ID
    Based on diagnostic: customfield_10016 is the editable Story Points field
    """
    if not story_points_value or str(story_points_value).strip() == "":
        return True
    
    try:
        # Use the correct Story Points field ID identified from diagnostics
        story_points_field = "customfield_10016"  # This is the editable one
        
        # First check if field is editable for this issue
        editable_fields = get_issue_editable_fields(base_url, session, issue_key)
        if story_points_field not in editable_fields:
            if logger:
                logger.warning(f"Story Points field {story_points_field} not editable for {issue_key}")
            return False
        
        update_url = f"{base_url}/rest/api/3/issue/{issue_key}"
        update_data = {"fields": {story_points_field: float(story_points_value)}}
        
        response = session.put(update_url, json=update_data)
        
        if response.status_code == 204:
            if logger:
                logger.info(f"✅ Updated Story Points for {issue_key}: {story_points_value}")
            return True
        else:
            if logger:
                logger.error(f"❌ Story Points update failed for {issue_key}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        if logger:
            logger.error(f"❌ Story Points update exception for {issue_key}: {e}")
        return False

def update_original_estimate_corrected(base_url, session, issue_key, original_estimate, logger=None):
    """
    Corrected Original Estimate update using alternative methods
    The timetracking field is not editable, so we'll try other approaches
    """
    if not original_estimate or str(original_estimate).strip() == "":
        return True
    
    # Convert time to seconds if it's in string format
    estimate_seconds = convert_time_to_seconds(original_estimate)
    if estimate_seconds is None:
        if logger:
            logger.warning(f"Could not parse time estimate '{original_estimate}' for {issue_key}")
        return False
    
    try:
        # Method 1: Try timeoriginalestimate field
        editable_fields = get_issue_editable_fields(base_url, session, issue_key)
        
        # Check various possible field names for Original Estimate
        possible_fields = [
            'timeoriginalestimate',
            'timetracking', 
            'customfield_10275',  # Estimated Effort
            'customfield_10157',  # Estimated Dev Effort (Hrs)
            'customfield_10155'   # Estimated QA Effort (Hrs)
        ]
        
        for field_id in possible_fields:
            if field_id in editable_fields:
                update_url = f"{base_url}/rest/api/3/issue/{issue_key}"
                
                if field_id == 'timetracking':
                    update_data = {"fields": {"timetracking": {"originalEstimate": str(original_estimate).strip()}}}
                elif field_id == 'timeoriginalestimate':
                    update_data = {"fields": {"timeoriginalestimate": estimate_seconds}}
                else:
                    # For custom fields, try string format first
                    update_data = {"fields": {field_id: str(original_estimate).strip()}}
                
                response = session.put(update_url, json=update_data)
                
                if response.status_code == 204:
                    if logger:
                        logger.info(f"✅ Updated Original Estimate for {issue_key} using {field_id}: {original_estimate}")
                    return True
                else:
                    if logger:
                        logger.debug(f"Field {field_id} failed for {issue_key}: {response.status_code}")
                    continue
        
        # If all methods fail, log the issue
        if logger:
            logger.warning(f"❌ No editable Original Estimate field found for {issue_key}. Available fields: {list(editable_fields.keys())}")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Original Estimate update exception for {issue_key}: {e}")
        return False

def test_corrected_updates():
    """Test the corrected update methods"""
    base_url = os.getenv('JIRA_URL')
    email = os.getenv('JIRA_EMAIL')
    token = os.getenv('JIRA_TOKEN')
    
    if not all([base_url, email, token]):
        print("❌ Missing JIRA credentials in .env file")
        return
    
    session = requests.Session()
    session.auth = (email, token)
    
    # Test issue
    test_issue = "CPESG-3239"
    
    print("🧪 Testing Corrected Field Updates")
    print("=" * 40)
    
    # Test Story Points
    print(f"📊 Testing Story Points update on {test_issue}")
    success = update_story_points_corrected(base_url, session, test_issue, 2)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test Original Estimate  
    print(f"⏱️  Testing Original Estimate update on {test_issue}")
    success = update_original_estimate_corrected(base_url, session, test_issue, "45m")
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n🏁 Testing complete!")

if __name__ == "__main__":
    test_corrected_updates()
