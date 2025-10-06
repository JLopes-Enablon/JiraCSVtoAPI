#!/usr/bin/env python3
"""
Test to verify CSV behavior:
- Source CSV (output.csv) should NOT be modified with Created Issue IDs
- Only tracker.csv should get the Created Issue IDs
"""

import os
import csv
import shutil
from jiraapi import import_stories_and_subtasks

def test_csv_behavior():
    """Test that source CSV remains unchanged and only tracker.csv gets Created Issue IDs"""
    
    # Create a test CSV without Created Issue ID
    test_csv_content = """Project,Summary,IssueType,Parent,Start Date,Story Points,Original Estimate,Time spent,Priority
CPESG,TEST CSV BEHAVIOR - Source Should Not Change,Story,,2025-10-06,1.0,1h,1h,Medium"""
    
    test_csv_path = "test_csv_behavior.csv"
    with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    # Read original content for comparison
    with open(test_csv_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    print("📋 Original CSV content:")
    print(original_content)
    print()
    
    # Backup tracker.csv if it exists
    tracker_path = "output/tracker.csv"
    tracker_backup = None
    if os.path.exists(tracker_path):
        tracker_backup = f"{tracker_path}.backup"
        shutil.copy2(tracker_path, tracker_backup)
    
    try:
        # Run the import process
        print("🚀 Running import process...")
        result = import_stories_and_subtasks(test_csv_path)
        
        # Check if source CSV was modified
        with open(test_csv_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        print("📋 CSV content after import:")
        print(modified_content)
        print()
        
        # Verify source CSV unchanged
        if original_content == modified_content:
            print("✅ SUCCESS: Source CSV remains unchanged!")
        else:
            print("❌ FAILURE: Source CSV was modified!")
            print("ORIGINAL:", repr(original_content))
            print("MODIFIED:", repr(modified_content))
            return False
        
        # Check tracker.csv for new entries
        if os.path.exists(tracker_path):
            with open(tracker_path, 'r', encoding='utf-8') as f:
                tracker_content = f.read()
            
            print("📊 Tracker.csv content:")
            print(tracker_content)
            
            # Look for our test item
            if "TEST CSV BEHAVIOR" in tracker_content and "CPESG-" in tracker_content:
                print("✅ SUCCESS: New issue properly added to tracker.csv!")
                return True
            else:
                print("❌ FAILURE: New issue not found in tracker.csv")
                return False
        else:
            print("❌ FAILURE: tracker.csv was not created")
            return False
            
    finally:
        # Cleanup
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        
        # Restore tracker backup if it existed
        if tracker_backup and os.path.exists(tracker_backup):
            shutil.move(tracker_backup, tracker_path)

if __name__ == "__main__":
    print("🧪 Testing CSV Behavior - Source Unchanged, Tracker Updated\n")
    success = test_csv_behavior()
    print(f"\n{'🎉 TEST PASSED' if success else '💥 TEST FAILED'}")