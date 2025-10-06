#!/usr/bin/env python3
"""
Test the fixed resolution setting with a single CSV line
"""
import os
import csv
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_single_csv_line():
    """Test creating and closing a single work item with proper resolution"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    project_id = os.getenv("JIRA_PROJECT_ID", "PROJ")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    print("Testing Fixed Resolution Setting")
    print("=" * 50)
    
    # Read first line from output.csv for testing
    csv_file = "/Users/jorge.lopez/Library/CloudStorage/OneDrive-WoltersKluwer/Documents/GitHub/Jira Api/JiraCSVtoAPI/output/output.csv"
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            first_row = next(reader)
            
            print(f"Test data from CSV:")
            print(f"  Summary: {first_row.get('Summary', 'N/A')}")
            print(f"  Issue Type: {first_row.get('IssueType', 'N/A')}")
            print(f"  Project: {first_row.get('Project', 'N/A')}")
            
            # Create a test version of this issue
            test_summary = f"TEST FIXED RESOLUTION - {first_row.get('Summary', 'Unknown')} (DELETE AFTER TESTING)"
            issue_type = first_row.get('IssueType', 'Story')
            
            print(f"\\nCreating test issue...")
            test_issue = jira.create_issue(
                project_key=project_id,
                summary=test_summary,
                issue_type=issue_type,
                assignee=None
            )
            
            issue_key = test_issue["key"]
            print(f"✓ Created: {issue_key}")
            
            # Test the transition with the fixed resolution setting
            print(f"\\nTesting transition to 'Closed' with resolution...")
            success = jira.transition_issue(issue_key, "Closed")
            
            if success:
                print("✅ Transition successful!")
                
                # Verify final state
                final_issue = jira.get_issue(issue_key)
                final_status = final_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                final_resolution = final_issue.get("fields", {}).get("resolution")
                final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                
                print(f"\\nFINAL VERIFICATION:")
                print(f"Status: {final_status}")
                print(f"Resolution: {final_resolution_name}")
                
                if final_resolution_name != "Unresolved":
                    print(f"\\n🎉 SUCCESS! Resolution properly set to '{final_resolution_name}'")
                    print("The fix is working correctly!")
                    return True, issue_key
                else:
                    print(f"\\n❌ Still showing 'Unresolved' - something is wrong")
                    return False, issue_key
            else:
                print("❌ Transition failed")
                return False, issue_key
                
    except FileNotFoundError:
        print(f"❌ Could not find CSV file: {csv_file}")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

if __name__ == "__main__":
    success, issue_key = test_single_csv_line()
    
    print("\\n" + "=" * 50)
    if success:
        print("✅ TEST PASSED - Resolution setting is now working!")
        print("Your main script should now work correctly.")
    else:
        print("❌ TEST FAILED - Further investigation needed")
    
    if issue_key:
        print(f"\\nTest issue created: {issue_key}")
        print("Please delete this manually from Jira UI when done testing")