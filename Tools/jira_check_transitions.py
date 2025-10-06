import sys
import os
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
"""
jira_check_transitions.py

Check available transitions for a Jira issue to understand workflow options.

Usage:
    python jira_check_transitions.py [issue_key]

Example:
    python jira_check_transitions.py PROJ-3239
"""
import os
from dotenv import load_dotenv
from jiraapi import JiraAPI

def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

def check_transitions(jira, issue_key):
    """Check available transitions for an issue"""
    try:
        # Get current status
        current_status = jira.get_issue_status(issue_key)
        print(f"Issue: {issue_key}")
        print(f"Current Status: {current_status}")
        
        # Get available transitions
        url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = jira.session.get(url)
        jira._handle_response(resp)
        transitions = resp.json().get("transitions", [])
        
        if transitions:
            print(f"\nAvailable Transitions:")
            for i, transition in enumerate(transitions, 1):
                to_status = transition.get("to", {}).get("name", "Unknown")
                print(f"  {i}. {transition['name']} → {to_status}")
        else:
            print("\nNo transitions available for this issue.")
            
    except Exception as e:
        print(f"Error checking transitions for {issue_key}: {e}")

def main():
    import sys
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("Usage: python jira_check_transitions.py [issue_key]")
        print("Example: python jira_check_transitions.py PROJ-3239")
        return
    
    issue_key = sys.argv[1]
    
    try:
        jira_url = get_env_var("JIRA_URL")
        jira_email = get_env_var("JIRA_EMAIL")
        jira_token = get_env_var("JIRA_TOKEN")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    jira = JiraAPI(jira_url, jira_email, jira_token)
    check_transitions(jira, issue_key)

if __name__ == "__main__":
    main()
