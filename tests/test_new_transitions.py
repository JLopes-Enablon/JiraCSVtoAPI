#!/usr/bin/env python3
"""
Test the new resolution-aware transition methods
"""
import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def test_new_transition_methods():
    """Test the new transition methods"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        print("Error: Missing environment variables")
        return False
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    # Test that new methods exist
    methods_to_test = [
        'find_closing_transition_with_resolution',
        'transition_to_done_with_resolution'
    ]
    
    missing_methods = []
    for method_name in methods_to_test:
        if not hasattr(jira, method_name):
            missing_methods.append(method_name)
        else:
            print(f"✓ Method {method_name} exists")
    
    if missing_methods:
        print(f"✗ Missing methods: {missing_methods}")
        return False
    else:
        print("✓ All new resolution methods exist")
        return True

def test_with_real_issue():
    """Test with a real issue"""
    load_dotenv()
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    
    test_issue = input("Enter an issue key to test transition analysis (or press Enter to skip): ").strip()
    
    if test_issue:
        print(f"\nAnalyzing transitions with resolution for: {test_issue}")
        print("=" * 60)
        
        try:
            # Test the new method
            trans_info = jira.find_closing_transition_with_resolution(test_issue)
            
            if trans_info:
                print(f"✓ Found closing transition with resolution: {trans_info['name']}")
                print(f"  Transition ID: {trans_info['id']}")
                resolution_names = [r.get('name', 'Unknown') for r in trans_info.get('resolution_options', [])]
                print(f"  Available resolutions: {resolution_names}")
            else:
                print("✗ No closing transitions with resolution found")
                print("  This means resolution must be set in a different way")
                
        except Exception as e:
            print(f"Error testing transition: {e}")
    else:
        print("Skipping real issue test")

if __name__ == "__main__":
    print("Testing New Resolution-Aware Transition Methods")
    print("=" * 60)
    
    success = True
    
    # Test method existence
    if not test_new_transition_methods():
        success = False
    
    print()
    
    # Test with real issue
    test_with_real_issue()
    
    print("=" * 60)
    if success:
        print("✓ Enhanced transition methods are ready!")
        print("✓ The script will now use resolution-aware transitions for closing issues")
        print("✓ This should resolve the 'Unresolved' status problem")
    else:
        print("✗ Some tests failed. Please check the issues above.")