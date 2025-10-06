#!/usr/bin/env python3
"""
Test the tracker.csv append functionality with a single item
"""
import os
import csv
import tempfile
from dotenv import load_dotenv
from jiraapi import JiraAPI, import_stories_and_subtasks

def test_tracker_append():
    """Test that tracker.csv only gets newly created items appended"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    if not all([jira_url, jira_email, jira_token]):
        print("❌ Missing environment variables")
        return False
    
    print("Testing Tracker Append Functionality")
    print("=" * 50)
    
    # Create a temporary test CSV with one item
    test_csv_content = """Project,Summary,IssueType,Parent,Start Date,Story Points,Original Estimate,Time spent,Priority,Created Issue ID
PROJ,TEST TRACKER - Single Item Test (DELETE AFTER),Story,,2025-10-06,1.0,1h,1h,Medium,"""
    
    # Write test CSV to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(test_csv_content)
        temp_csv_path = temp_file.name
    
    try:
        print(f"Created test CSV: {temp_csv_path}")
        
        # Count current tracker entries
        tracker_path = "/Users/jorge.lopez/Library/CloudStorage/OneDrive-WoltersKluwer/Documents/GitHub/Jira Api/JiraCSVtoAPI/output/tracker.csv"
        initial_count = 0
        if os.path.exists(tracker_path):
            with open(tracker_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                initial_count = sum(1 for _ in reader)
        
        print(f"Initial tracker.csv entries: {initial_count}")
        
        # Create JiraAPI instance
        jira = JiraAPI(jira_url, jira_email, jira_token)
        
        # Run import - this should create one issue and append it to tracker
        print("Running import...")
        import_stories_and_subtasks(temp_csv_path, jira)
        
        # Count tracker entries after import
        final_count = 0
        if os.path.exists(tracker_path):
            with open(tracker_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                final_count = sum(1 for _ in reader)
        
        print(f"Final tracker.csv entries: {final_count}")
        
        # Check if exactly one entry was added
        entries_added = final_count - initial_count
        print(f"Entries added to tracker: {entries_added}")
        
        if entries_added == 1:
            print("✅ SUCCESS: Exactly 1 entry added to tracker.csv")
            
            # Verify the last entry is our test item
            with open(tracker_path, 'r', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))
                last_entry = reader[-1]
                if "TEST TRACKER" in last_entry.get('Summary', ''):
                    print("✅ SUCCESS: Correct test item was appended")
                    issue_key = last_entry.get('Created Issue ID')
                    print(f"Created Issue ID: {issue_key}")
                    return True, issue_key
                else:
                    print("❌ FAILED: Wrong item appended to tracker")
                    return False, None
        else:
            print(f"❌ FAILED: Expected 1 entry added, got {entries_added}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, None
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_csv_path)
        except:
            pass

if __name__ == "__main__":
    success, issue_key = test_tracker_append()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TRACKER TEST PASSED!")
        print("The tracker.csv append functionality is working correctly.")
        if issue_key:
            print(f"\nTest issue created: {issue_key}")
            print("Please delete this from Jira UI when convenient.")
    else:
        print("❌ TRACKER TEST FAILED")
        print("The tracker.csv append functionality needs further debugging.")