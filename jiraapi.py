"""
jiraapi.py

Main Jira API integration and bulk import script.
- Handles importing issues and sub-tasks from CSV files (work item or calendar exports)
- Creates issues and sub-tasks in Jira using REST API
- Updates Story Points, Original Estimate, Start Date, and other fields
- Maps CSV columns to Jira fields, including custom fields
- Handles field editability via Jira's editmeta endpoint
- Usage: Run via main menu or directly for bulk import
"""

import requests
import os
import csv
import logging
import re
from dotenv import load_dotenv
from typing import Any, Dict, Optional
# Field mapping utility
import subprocess
import json
from pathlib import Path
import tempfile


# -------------------------------------------------------------
# Custom Field Defaults Management
# -------------------------------------------------------------

def load_custom_field_defaults() -> dict:
    """
    Load custom field defaults from environment variables.
    Environment variables should be in format: FIELD_<FIELD_NAME>=<value>
    
    Returns:
        Dictionary mapping field names to their default values
    """
    defaults = {}
    
    # Field ID mapping - maps friendly names to Jira field IDs
    field_mapping = {
        'DIVISION': 'customfield_10255',
        'BUSINESS_UNIT': 'customfield_10160', 
        'TASK_TYPE': 'customfield_10609',
        'IPM_MANAGED': 'customfield_10606',
        'LABELS': 'labels',
        'ENVIRONMENT': 'customfield_10153',
        'GBS_SERVICE': 'customfield_10605',
        'TASK_SUB_TYPE': 'customfield_10610'
    }
    
    load_dotenv()  # Ensure environment variables are loaded
    
    for env_key, field_id in field_mapping.items():
        env_var = f"FIELD_{env_key}"
        value = os.getenv(env_var)
        
        if value:
            # Process the value based on field type
            if field_id == 'labels':
                # Labels should be an array of strings
                defaults[field_id] = [label.strip() for label in value.split(',')]
            else:
                # Custom fields typically need option format for dropdowns
                defaults[field_id] = {"value": value}
            
            print(f"🔧 Loaded default for {env_key}: {value}")
    
    return defaults


# -------------------------------------------------------------
# JiraAPI: Main class for interacting with Jira REST API
# -------------------------------------------------------------

# -------------------------------------------------------------
# JiraAPI: Main class for interacting with Jira REST API
# -------------------------------------------------------------
class JiraAPI:

    def transition_issue(self, issue_key: str, transition_name: str = "Closed") -> bool:
        """
        Transition a Jira issue to a new status by name (e.g., Closed, Done, In Progress, Backlog).
        Uses /transitions endpoint to find and perform the transition.
        If the exact transition is not found, tries common alternatives.
        For closing transitions, automatically sets resolution to "Done".
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
            transition_name: The name of the transition to perform (default: 'Closed').
        Returns:
            True if transition was successful, False otherwise.
        """
        try:
            # Get available transitions with field details
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            # CRITICAL: Must use expand=transitions.fields to get resolution field access
            params = {"expand": "transitions.fields"}
            resp = self.session.get(url, params=params)
            self._handle_response(resp)
            transitions = resp.json().get("transitions", [])
            
            # Create a list of available transition names
            available_transitions = [t["name"] for t in transitions]
            
            # Handle special case for "close_by_type" - find the best close transition
            if transition_name == "close_by_type":
                # Priority order for close transitions
                close_options = ["Done", "Closed", "Resolve", "Complete", "Finished"]
                transition_name = None
                for close_option in close_options:
                    if any(t["name"].lower() == close_option.lower() for t in transitions):
                        transition_name = close_option
                        break
                
                if not transition_name:
                    self.logger.warning(f"No suitable close transition found for {issue_key}. Available: {', '.join(available_transitions)}")
                    return False
            
            # Find the transition by name (case-insensitive)
            transition = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
            
            # If exact match not found, try alternatives
            if not transition:
                alternatives = {
                    "done": ["Closed", "Complete", "Resolve", "Finished"],
                    "closed": ["Done", "Complete", "Resolve", "Finished"],
                    "complete": ["Done", "Closed", "Resolve", "Finished"],
                    "resolve": ["Done", "Closed", "Complete", "Finished"]
                }
                
                for alt in alternatives.get(transition_name.lower(), []):
                    transition = next((t for t in transitions if t["name"].lower() == alt.lower()), None)
                    if transition:
                        self.logger.info(f"Using alternative transition '{alt}' instead of '{transition_name}' for {issue_key}")
                        transition_name = alt
                        break
            
            if not transition:
                available = ", ".join(available_transitions)
                self.logger.warning(f"Transition '{transition_name}' not found for {issue_key}. Available: {available}")
                return False
                
            transition_id = transition["id"]
            
            # Check if this is a closing transition
            close_transition_names = ["done", "closed", "complete", "resolve", "finished"]
            is_closing_transition = transition_name.lower() in close_transition_names
            
            # Prepare transition data
            post_url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            transition_data = {"transition": {"id": transition_id}}
            
            # For closing transitions, always try to include resolution
            if is_closing_transition:
                transition_fields = transition.get("fields", {})
                if "resolution" in transition_fields:
                    resolution_options = transition_fields["resolution"].get("allowedValues", [])
                    
                    # Priority order for resolution values - prefer "Done" for closing
                    preferred_resolutions = ["Done", "Completed", "Fixed", "Resolved"]
                    selected_resolution = None
                    
                    for pref_res in preferred_resolutions:
                        for res_option in resolution_options:
                            if res_option.get("name", "").lower() == pref_res.lower():
                                selected_resolution = {"id": res_option["id"]}
                                self.logger.info(f"Setting resolution to '{pref_res}' for {issue_key}")
                                break
                        if selected_resolution:
                            break
                    
                    # If no preferred resolution found, use first available (not Unresolved)
                    if not selected_resolution and resolution_options:
                        for res_option in resolution_options:
                            if res_option.get("name", "").lower() != "unresolved":
                                selected_resolution = {"id": res_option["id"]}
                                self.logger.info(f"Using fallback resolution '{res_option.get('name')}' for {issue_key}")
                                break
                    
                    # Add resolution to transition data if we found one
                    if selected_resolution:
                        transition_data["fields"] = {"resolution": selected_resolution}
                    else:
                        self.logger.warning(f"No suitable resolution found for {issue_key}, transition may set to Unresolved")
                else:
                    self.logger.warning(f"No resolution field available for transition '{transition_name}' on {issue_key}")
            
            # Perform the transition
            post_resp = self.session.post(post_url, json=transition_data)
            
            if post_resp.ok:
                self.logger.info(f"Successfully transitioned {issue_key} to '{transition_name}'")
                
                if is_closing_transition:
                    # Verify the final status and resolution
                    verification_issue = self.get_issue(issue_key)
                    final_status = verification_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                    final_resolution = verification_issue.get("fields", {}).get("resolution")
                    final_resolution_name = final_resolution.get("name") if final_resolution else "Unresolved"
                    
                    if final_resolution_name == "Unresolved":
                        self.logger.warning(f"Issue {issue_key} closed but resolution remains 'Unresolved'")
                        self.logger.warning("This may indicate a workflow configuration issue")
                    else:
                        self.logger.info(f"✅ Issue {issue_key} successfully closed with resolution: {final_resolution_name}")
                
                return True
            else:
                error_msg = f"Failed to transition {issue_key} to '{transition_name}': {post_resp.status_code} {post_resp.text}"
                self.logger.error(error_msg)
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to transition {issue_key} to '{transition_name}': {e}")
            return False
            
    def find_closing_transition_with_resolution(self, issue_key: str) -> dict:
        """
        Find a transition that leads to a closed state AND allows setting resolution.
        This is crucial because many Jira configurations only allow resolution 
        to be set during specific transitions, not as a separate field update.
        
        Args:
            issue_key: The Jira issue key
        Returns:
            Dict with transition info and resolution options, or empty dict if none found
        """
        try:
            # Get available transitions
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
            resp = self.session.get(url)
            self._handle_response(resp)
            transitions = resp.json().get("transitions", [])
            
            # Look for transitions that have resolution field AND lead to closed states
            closing_transitions_with_resolution = []
            
            for transition in transitions:
                trans_name = transition.get("name", "").lower()
                trans_fields = transition.get("fields", {})
                
                # Check if this transition leads to a closed state
                is_closing = any(keyword in trans_name for keyword in 
                               ["done", "closed", "complete", "resolve", "finish"])
                
                # Check if resolution field is available in this transition
                has_resolution = "resolution" in trans_fields
                
                if is_closing and has_resolution:
                    resolution_options = trans_fields["resolution"].get("allowedValues", [])
                    closing_transitions_with_resolution.append({
                        "transition": transition,
                        "name": transition.get("name"),
                        "id": transition.get("id"),
                        "resolution_options": resolution_options
                    })
            
            # Return the best option (prefer "Done" > "Closed" > others)
            priority_order = ["done", "closed", "complete", "resolve", "finish"]
            for priority in priority_order:
                for trans_info in closing_transitions_with_resolution:
                    if priority in trans_info["name"].lower():
                        self.logger.info(f"Found closing transition with resolution: {trans_info['name']} for {issue_key}")
                        return trans_info
            
            # If no priority match, return the first one found
            if closing_transitions_with_resolution:
                return closing_transitions_with_resolution[0]
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to find closing transition with resolution for {issue_key}: {e}")
            return {}

    def transition_to_done_with_resolution(self, issue_key: str, resolution_name: str = "Done") -> bool:
        """
        Transition an issue to a closed state while setting the resolution.
        This method finds transitions that allow both status change and resolution setting.
        If no such transition exists, it tries a multi-step approach.
        
        Args:
            issue_key: The Jira issue key
            resolution_name: Preferred resolution name (default: "Done")
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, check current status
            issue = self.get_issue(issue_key)
            current_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
            
            # If already closed, try to set resolution directly
            closed_statuses = ["done", "closed", "complete", "resolved", "finished"]
            if current_status.lower() in closed_statuses:
                self.logger.info(f"{issue_key} is already closed ({current_status}), attempting to set resolution")
                return self.set_resolution(issue_key, resolution_name)
            
            # Find a transition that supports resolution setting
            trans_info = self.find_closing_transition_with_resolution(issue_key)
            
            if trans_info:
                # Found a transition with resolution - use it
                resolution_options = trans_info["resolution_options"]
                selected_resolution = None
                
                # Priority order for resolution values
                preferred_resolutions = [resolution_name, "Done", "Completed", "Fixed", "Resolved"]
                
                for pref_res in preferred_resolutions:
                    for res_option in resolution_options:
                        if res_option.get("name", "").lower() == pref_res.lower():
                            selected_resolution = {"id": res_option["id"]}
                            self.logger.info(f"Will set resolution to '{pref_res}' for {issue_key}")
                            break
                    if selected_resolution:
                        break
                
                # If no preferred resolution found, use the first available
                if not selected_resolution and resolution_options:
                    first_resolution = resolution_options[0]
                    selected_resolution = {"id": first_resolution["id"]}
                    self.logger.info(f"Using first available resolution '{first_resolution.get('name', 'Unknown')}' for {issue_key}")
                
                if not selected_resolution:
                    self.logger.warning(f"No resolution options available for transition {trans_info['name']} on {issue_key}")
                    return self.transition_issue(issue_key, "Closed")
                
                # Perform the transition with resolution
                post_url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
                transition_data = {
                    "transition": {"id": trans_info["id"]},
                    "fields": {"resolution": selected_resolution}
                }
                
                self.logger.debug(f"Transition data for {issue_key}: {transition_data}")
                
                post_resp = self.session.post(post_url, json=transition_data)
                self._handle_response(post_resp)
                
                self.logger.info(f"Successfully transitioned {issue_key} to '{trans_info['name']}' with resolution")
                return True
            else:
                # No transition with resolution found - try alternative approach
                self.logger.info(f"No resolution-aware transition found for {issue_key}, using fallback approach")
                
                # Step 1: Transition to closed state
                success = self.transition_issue(issue_key, "Closed")
                if not success:
                    return False
                
                # Step 2: Try to set resolution after transition
                # Note: This might not work in all Jira configurations
                return self.set_resolution(issue_key, resolution_name)
            
        except Exception as e:
            self.logger.error(f"Failed to transition {issue_key} to done with resolution: {e}")
            return False
    
    def get_available_resolutions(self, issue_key: str) -> list:
        """
        Get available resolution values for an issue.
        Args:
            issue_key: The Jira issue key.
        Returns:
            List of available resolution options.
        """
        try:
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/editmeta"
            resp = self.session.get(url)
            self._handle_response(resp)
            editmeta = resp.json()
            
            resolution_field = editmeta.get("fields", {}).get("resolution", {})
            return resolution_field.get("allowedValues", [])
        except Exception as e:
            self.logger.error(f"Failed to get available resolutions for {issue_key}: {e}")
            return []

    def set_resolution(self, issue_key: str, resolution_name: str = "Done") -> bool:
        """
        Set the resolution field for an issue without changing its status.
        Args:
            issue_key: The Jira issue key.
            resolution_name: The resolution to set (default: 'Done').
        Returns:
            True if resolution was set successfully, False otherwise.
        """
        try:
            # Get available resolutions
            available_resolutions = self.get_available_resolutions(issue_key)
            
            # Find the resolution by name
            resolution = next(
                (r for r in available_resolutions if r.get("name", "").lower() == resolution_name.lower()), 
                None
            )
            
            if not resolution:
                # Try common alternatives
                alternatives = ["Done", "Completed", "Fixed", "Resolved"]
                for alt in alternatives:
                    resolution = next(
                        (r for r in available_resolutions if r.get("name", "").lower() == alt.lower()), 
                        None
                    )
                    if resolution:
                        self.logger.info(f"Using alternative resolution '{alt}' instead of '{resolution_name}' for {issue_key}")
                        break
            
            if not resolution:
                available = [r.get("name", "Unknown") for r in available_resolutions]
                self.logger.warning(f"Resolution '{resolution_name}' not found for {issue_key}. Available: {available}")
                return False
            
            # Update the resolution field
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            data = {"fields": {"resolution": {"id": resolution["id"]}}}
            resp = self.session.put(url, json=data)
            self._handle_response(resp)
            
            self.logger.info(f"Set resolution to '{resolution['name']}' for {issue_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set resolution for {issue_key}: {e}")
            return False
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """
        Initialize the JiraAPI client and session.
        Args:
            base_url: The base URL of the Jira instance.
            email: Jira user email for authentication.
            api_token: Jira API token for authentication.
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Retrieve a Jira issue by its key using /issue/{key} endpoint.
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
        Returns:
            The issue data as a dictionary.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        self.logger.debug(f"Fetching issue: {issue_key} from {url}")
        response = self.session.get(url)
        self._handle_response(response)
        self.logger.info(f"Fetched issue: {issue_key}")
        return response.json()

    def get_issue_status(self, issue_key: str) -> Optional[str]:
        """
        Get the current status of a Jira issue (e.g., 'To Do', 'In Progress', 'Done').
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
        Returns:
            The current status name, or None if issue not found.
        """
        try:
            issue = self.get_issue(issue_key)
            return issue.get("fields", {}).get("status", {}).get("name")
        except Exception as e:
            self.logger.error(f"Failed to get status for {issue_key}: {e}")
            return None

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Story", assignee: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
        """
        Create a new Jira issue with custom field defaults from .env file applied automatically.
        Custom field defaults are loaded from environment variables in format: FIELD_<NAME>=<value>
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the issue.
            issue_type: The type of issue (default: 'Story').
            assignee: (Optional) Assignee username (for legacy Jira only).
            **fields: Additional fields for the issue (these override defaults).
        Returns:
            The created issue data as a dictionary.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        
        # Start with basic required fields
        fields_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        
        if assignee:
            fields_dict["assignee"] = {"name": assignee}
        
        # Load and apply custom field defaults from .env
        try:
            custom_defaults = load_custom_field_defaults()
            if custom_defaults:
                self.logger.info(f"Applying {len(custom_defaults)} custom field defaults from .env")
                fields_dict.update(custom_defaults)
        except Exception as e:
            self.logger.warning(f"Failed to load custom field defaults: {e}")
        
        # Apply any explicitly provided fields (these override defaults)
        fields_dict.update(fields)
        
        data = {"fields": fields_dict}
        self.logger.info(f"Creating issue in project {project_key} with summary '{summary}'")
        self.logger.debug(f"Payload for issue creation: {data}")
        
        response = self.session.post(url, json=data)
        self._handle_response(response)
        issue_key = response.json().get("key", "<unknown>")
        self.logger.info(f"✅ Created issue: {issue_key} in project {project_key}")
        return response.json()

    def _update_assignee(self, issue_key: str, account_id: Optional[str] = None, name: Optional[str] = None) -> None:
        """
        Helper to update the assignee of an issue by accountId (Jira Cloud) or name (Jira Server/DC).
        Always uses 'id' if the value looks like an accountId (contains a colon or is a UUID).
        Args:
            issue_key: The Jira issue key.
            account_id: Jira Cloud accountId (preferred).
            name: Jira Server/DC username (fallback).
        """
        update_url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        update_data = None
        if account_id:
            # Use 'id' for Jira Cloud (accountId)
            update_data = {"fields": {"assignee": {"id": account_id}}}
            self.logger.info(f"Updating assignee for {issue_key} to accountId {account_id}")
        elif name:
            # If the name looks like an accountId, use 'id' instead
            if ":" in name or (len(name) >= 32 and all(c in '0123456789abcdef-' for c in name.replace(':','').replace('-',''))):
                update_data = {"fields": {"assignee": {"id": name}}}
                self.logger.info(f"Updating assignee for {issue_key} to accountId {name} (detected by format)")
            else:
                update_data = {"fields": {"assignee": {"name": name}}}
                self.logger.info(f"Updating assignee for {issue_key} to username {name}")
        else:
            self.logger.warning(f"No assignee info provided for {issue_key}. Skipping assignee update.")
            return
        self.logger.debug(f"Payload for assignee update: {update_data}")
        update_response = self.session.put(update_url, json=update_data)
        self._handle_response(update_response)
        self.logger.info(f"Updated assignee for {issue_key}")

    def log_work(self, issue_key: str, time_spent: str, comment: Optional[str] = None) -> None:
        """
        Log work (time spent) on an issue using the Jira worklog API.
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
            time_spent: The amount of time spent (e.g., '1h', '30m').
            comment: (Optional) Comment for the worklog entry.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/worklog"
        worklog_data = {"timeSpent": time_spent}
        if comment:
            worklog_data["comment"] = comment
        self.logger.info(f"Logging work for {issue_key}: {time_spent}")
        self.logger.debug(f"Payload for worklog: {worklog_data}")
        try:
            response = self.session.post(url, json=worklog_data)
            self.logger.debug(f"Worklog API response: {response.status_code} {response.text}")
            self._handle_response(response)
            self.logger.info(f"Logged work for {issue_key}")
        except Exception as e:
            self.logger.error(f"Failed to log work for {issue_key}: {e}")

    def create_subtask(
        self,
        project_key: str,
        summary: str,
        parent_key: str,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        **fields: Any
    ) -> Dict[str, Any]:
        """
        Create a Jira sub-task under a parent issue with custom field defaults applied.
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the sub-task.
            parent_key: The key of the parent story.
            assignee: (Optional) Assignee username (for legacy Jira only).
            priority: (Optional) Priority name.
            **fields: Additional fields for the sub-task (these override defaults).
        Returns:
            The created sub-task data as a dictionary.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        
        # Start with basic required fields
        subtask_fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": "Sub-task"},
            "parent": {"key": parent_key},
        }
        
        if assignee:
            subtask_fields["assignee"] = {"name": assignee}
        if priority:
            subtask_fields["priority"] = {"name": priority}
        
        # Load and apply custom field defaults from .env
        try:
            custom_defaults = load_custom_field_defaults()
            if custom_defaults:
                self.logger.info(f"Applying {len(custom_defaults)} custom field defaults to sub-task")
                subtask_fields.update(custom_defaults)
        except Exception as e:
            self.logger.warning(f"Failed to load custom field defaults for sub-task: {e}")
        
        # Apply any explicitly provided fields (these override defaults)
        subtask_fields.update(fields)
        
        data = {"fields": subtask_fields}
        self.logger.debug(f"Creating sub-task under parent {parent_key} in project {project_key} with summary '{summary}'")
        
        response = self.session.post(url, json=data)
        self._handle_response(response)
        subtask_key = response.json().get("key", "<unknown>")
        self.logger.info(f"✅ Created sub-task: {subtask_key} under parent {parent_key}")
        return response.json()

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Jira issue with the provided fields.
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
            fields: Dictionary of fields to update.
        Returns:
            The response from the API.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        data = {"fields": fields}
        
        self.logger.info(f"Updating issue {issue_key} with fields: {list(fields.keys())}")
        self.logger.debug(f"Update payload: {data}")
        
        response = self.session.put(url, json=data)
        self._handle_response(response)
        
        self.logger.info(f"Successfully updated issue {issue_key}")
        return response.json() if response.text else {}

    def update_issue_fields(self, issue_key: str, story_points=None, original_estimate=None, field_mapping=None, **kwargs):
        """
        Update issue fields with proper validation and field checking.
        This method handles Story Points, Original Estimate, and other custom fields safely.
        Args:
            issue_key: The Jira issue key.
            story_points: Story Points value to set.
            original_estimate: Original Estimate value to set.
            field_mapping: Mapping of field names to Jira field IDs.
            **kwargs: Additional fields to update.
        Returns:
            List of any errors encountered during the update.
        """
        errors = []
        try:
            # Get current issue data
            current = self.get_issue(issue_key)
            current_fields = current.get("fields", {})
        except Exception as e:
            error_msg = f"Failed to fetch current issue {issue_key}: {e}"
            self.logger.error(error_msg)
            return [error_msg]

        update_fields = {}
        
        # Get editable fields for this issue
        editmeta_url = f"{self.base_url}/rest/api/3/issue/{issue_key}/editmeta"
        editmeta_response = self.session.get(editmeta_url)
        editable_fields = {}
        if editmeta_response.ok:
            editable_fields = editmeta_response.json().get('fields', {})
            self.logger.debug(f"Editable fields for {issue_key}: {list(editable_fields.keys())}")
        else:
            self.logger.warning(f"Failed to fetch editable fields for {issue_key}: {editmeta_response.status_code}")

        # Handle Story Points
        if story_points is not None and str(story_points).strip() not in ["", "none", "None"]:
            sp_fields_to_try = [
                field_mapping.get('Story Points', 'customfield_10146') if field_mapping else 'customfield_10146',
                'customfield_10016', 
                'customfield_10146'
            ]
            for sp_field in sp_fields_to_try:
                if sp_field in editable_fields:
                    try:
                        update_fields[sp_field] = float(story_points)
                        self.logger.info(f"Will update Story Points field {sp_field} for {issue_key} to {story_points}")
                        break
                    except ValueError:
                        self.logger.warning(f"Invalid Story Points value '{story_points}' for {issue_key}")
                        break
                else:
                    self.logger.debug(f"Story Points field {sp_field} not editable for {issue_key}")

        # Handle Original Estimate
        if original_estimate is not None and str(original_estimate).strip() not in ["", "none", "None"]:
            oe_fields_to_try = ["timetracking", "timeoriginalestimate"]
            for oe_field in oe_fields_to_try:
                if oe_field in editable_fields:
                    if oe_field == "timetracking":
                        update_fields[oe_field] = {"originalEstimate": str(original_estimate).strip()}
                    else:
                        update_fields[oe_field] = str(original_estimate).strip()
                    self.logger.info(f"Will update Original Estimate field {oe_field} for {issue_key} to {original_estimate}")
                    break
                else:
                    self.logger.debug(f"Original Estimate field {oe_field} not editable for {issue_key}")

        # Handle other fields from kwargs
        for field_name, field_value in kwargs.items():
            if field_name.lower() in ["time_spent", "time spent"]:
                continue  # Skip time spent, handle via worklog
            
            # Map field name to Jira field ID
            jira_field = field_mapping.get(field_name, field_name.replace(" ", "_")) if field_mapping else field_name.replace(" ", "_")
            
            # Special handling for certain fields
            if field_name.lower() == "priority":
                if jira_field in editable_fields and field_value:
                    update_fields["priority"] = {"name": field_value}
            elif field_name.lower() == "parent":
                if jira_field in editable_fields and field_value:
                    update_fields["parent"] = {"key": field_value}
            elif field_name.lower() == "components":
                if jira_field in editable_fields and field_value:
                    comps = [c.strip() for c in str(field_value).split(",") if c.strip()]
                    update_fields["components"] = [{"name": c} for c in comps]
            elif field_name.lower() == "labels":
                if jira_field in editable_fields and field_value:
                    labels = [l.strip() for l in str(field_value).split(",") if l.strip()]
                    update_fields["labels"] = labels
            else:
                # Generic field handling
                if jira_field in editable_fields and field_value is not None:
                    current_value = current_fields.get(jira_field)
                    if str(field_value) != str(current_value):
                        update_fields[jira_field] = field_value

        # Perform the update if there are fields to update
        if update_fields:
            try:
                self.update_issue(issue_key, update_fields)
                self.logger.info(f"Successfully updated {issue_key} with fields: {list(update_fields.keys())}")
            except Exception as e:
                error_msg = f"Failed to update {issue_key}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        else:
            self.logger.info(f"No updates needed for {issue_key}")

        return errors

    def _handle_response(self, response: requests.Response) -> None:
        """
        Handle the HTTP response from the Jira API, raising exceptions for errors.
        Args:
            response: The HTTP response object.
        Raises:
            Exception: If the response status is not OK.
        """
        if not response.ok:
            self.logger.error(f"Jira API error: {response.status_code} {response.text}")
            raise Exception(f"Jira API error: {response.status_code} {response.text}")

# End of JiraAPI class



###############################################################
# import_stories_and_subtasks: Main bulk import workflow
###############################################################
def import_stories_and_subtasks(csv_path: str, jira: JiraAPI, field_mapping=None) -> None:
    """
    Import stories and sub-tasks from a CSV file into Jira.
    Expects CSV with columns: Project, Summary, IssueType, Parent, Start Date, Story Points, Original Estimate, Time spent, Priority.
    Assignee is read from the environment variable JIRA_ASSIGNEE.
    Trims whitespace and matches parent stories case-insensitively.
    Only creates sub-tasks if their parent story is defined in the CSV.
    Args:
        csv_path: Path to the CSV file.
        jira: JiraAPI instance.
        field_mapping: dict of {system_field: custom_field_id}
    """
    logger = logging.getLogger("JiraImport")
    assignee_env = os.getenv("JIRA_ASSIGNEE")
    project_id_env = os.getenv("JIRA_PROJECT_ID")

    # Prepare lists for processing
    top_level_issues = []  # List of (idx, row) for non-sub-task issues
    subtasks = []          # List of (idx, row) for sub-tasks
    all_rows = []          # All rows from the CSV

    # Track which rows were initially empty (for tracker.csv)
    initially_empty_indices = set()
    
    # Read and classify rows from the CSV file
    # Only process rows that have not yet been imported (no Created Issue ID)
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for idx, row in enumerate(reader):
            all_rows.append(row)
            # Only process rows that have not yet been imported (no Created Issue ID)
            if not row.get("Created Issue ID"):
                initially_empty_indices.add(idx)
                issue_type = (row.get("IssueType") or "").strip().lower()
                if issue_type == "sub-task":
                    # Collect sub-tasks for later processing
                    subtasks.append((idx, row))
                else:
                    # Collect all other issue types (Story, Task, Bug, etc.)
                    top_level_issues.append((idx, row))

    # Build a map for parent lookup: Jira key and summary (lowercased) to Jira key
    # This allows sub-tasks to find their parent by key or summary
    issue_map: Dict[str, str] = {}
    for row in all_rows:
        issue_type = (row.get("IssueType") or "").strip().lower()
        if row.get("Created Issue ID") and issue_type != "sub-task":
            summary_key = (row["Summary"] or "").strip().lower()
            issue_map[row["Created Issue ID"]] = row["Created Issue ID"]
            issue_map[summary_key] = row["Created Issue ID"]

    # Dynamically query available close transitions for each issue type
    print("\nQuerying available close transitions for each issue type...")
    issue_types_to_check = ["Epic", "Story", "Task", "Sub-task"]
    close_transitions = {}
    sample_issue_keys = {}
    # Find a sample issue key for each type (from all_rows)
    for t in issue_types_to_check:
        for row in all_rows:
            if (row.get("IssueType") or "").strip().lower() == t.lower() and row.get("Created Issue ID"):
                sample_issue_keys[t] = row["Created Issue ID"]
                break
    for t, key in sample_issue_keys.items():
        try:
            url = f"{jira.base_url}/rest/api/3/issue/{key}/transitions"
            resp = jira.session.get(url)
            transitions = resp.json().get("transitions", [])
            close_names = [tr["name"] for tr in transitions if tr["name"].lower() in ["closed", "done"]]
            close_transitions[t] = close_names if close_names else [tr["name"] for tr in transitions]
        except Exception as e:
            close_transitions[t] = []
    print("\nAvailable close transitions by issue type:")
    for t in issue_types_to_check:
        print(f"  {t}: {close_transitions.get(t, [])}")
    print("\nSelect a status transition mode for created issues:")
    print("  1. Use default close for each type (prompt for each issue)")
    print("  2. In Progress (prompt for each issue)")
    print("  3. Backlog (prompt for each issue)")
    print("  4. Close All (all issues will be marked as close for their type, no further prompts)")
    print("  5. In Progress All (all issues will be marked as In Progress, no further prompts)")
    print("  6. Backlog All (all issues will be marked as Backlog, no further prompts)")
    mode_choice = input("Choose [1-6] or press Enter for default: ").strip()
    if mode_choice == "4":
        transition_mode = "all"
        transition_all_status = "close_by_type"
        transition_default = "close_by_type"
    elif mode_choice == "5":
        transition_mode = "all"
        transition_all_status = "In Progress"
        transition_default = "In Progress"
    elif mode_choice == "6":
        transition_mode = "all"
        transition_all_status = "Backlog"
        transition_default = "Backlog"
    elif mode_choice == "2":
        transition_mode = "prompt"
        transition_default = "In Progress"
    elif mode_choice == "3":
        transition_mode = "prompt"
        transition_default = "Backlog"
    else:
        transition_mode = "prompt"
        transition_default = "close_by_type"

    # Create all top-level issues (Story, Task, etc.)
    # For each, create in Jira, update mapping, and perform post-creation updates
    for idx, row in top_level_issues:
        summary_clean = (row["Summary"] or "").strip()
        issue_type = (row.get("IssueType") or "Story").strip()
        sp_field = field_mapping.get('Story Points', 'customfield_10016') if field_mapping else 'customfield_10016'
        sp_value = row.get("Story Points") or row.get("Story point estimate")
        # Use project from .env if available, else from CSV, and save to .env if not set
        project_val = project_id_env or row["Project"]
        if not project_id_env:
            from dotenv import set_key
            env_path = Path(__file__).parent / '.env'
            set_key(str(env_path), "JIRA_PROJECT_ID", project_val)
            project_id_env = project_val
        # Create the issue in Jira (minimal fields)
        issue = jira.create_issue(
            project_key=project_val,
            summary=summary_clean,
            issue_type=issue_type,
            assignee=None
        )
        issue_key = issue["key"]
        # Add the new issue to the map for parent lookup
        issue_map[issue_key] = issue_key
        issue_map[summary_clean.lower()] = issue_key
        logger.info(f"Created {issue_type}: {issue_key}")
        all_rows[idx]["Created Issue ID"] = issue_key

        # === Post-creation updates for all issue types ===
        # Includes status transition, Story Points, Original Estimate, Start Date, Assignee, Time Spent, Parent

        # Transition logic (prompt or all)
        if transition_mode == "all":
            try:
                # Use resolution-aware transition for closing states
                if transition_all_status == "close_by_type":
                    jira.transition_to_done_with_resolution(issue_key, "Done")
                else:
                    jira.transition_issue(issue_key, transition_all_status)
            except Exception as e:
                logger.warning(f"Could not transition {issue_key} to '{transition_all_status}': {e}")
        elif transition_mode == "prompt":
            print(f"\nSelect a status transition for {issue_key} (default: {transition_default}):")
            print(f"  1. {transition_default} (default)")
            print("  2. In Progress")
            print("  3. Backlog")
            print("  4. Enter custom transition name")
            print("  5. Skip status transition for this issue")
            choice = input("Choose [1-5] or press Enter for default: ").strip()
            if choice == "2":
                transition_name = "In Progress"
            elif choice == "3":
                transition_name = "Backlog"
            elif choice == "4":
                transition_name = input("Enter custom transition name: ").strip() or transition_default
            elif choice == "5":
                transition_name = None
            else:
                transition_name = transition_default
            if transition_name:
                try:
                    # Use resolution-aware transition for closing states
                    if transition_name.lower() in ["close_by_type", "done", "closed", "complete", "resolve", "finished"]:
                        jira.transition_to_done_with_resolution(issue_key, "Done")
                    else:
                        jira.transition_issue(issue_key, transition_name)
                except Exception as e:
                    logger.warning(f"Could not transition {issue_key} to '{transition_name}': {e}")
        # 1. Story Points (for all issue types and sub-tasks if allowed)
        # Only update if editable and value present
        allow_update_sp = True
        if issue_type.lower() == "sub-task" and field_mapping and isinstance(field_mapping, dict):
            allow_update_sp = field_mapping.get('Allow Story Points ', False)
        if allow_update_sp and sp_field and sp_value is not None and str(sp_value).strip() != "":
            try:
                # Use the selected editable Story Points field
                correct_sp_field = sp_field
                # Check if the issue allows Story Points updates
                editmeta_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/editmeta"
                editmeta_response = jira.session.get(editmeta_url)
                if editmeta_response.ok:
                    editable_fields = editmeta_response.json().get('fields', {})
                    if correct_sp_field in editable_fields:
                        update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                        update_data = {"fields": {correct_sp_field: float(sp_value)}}
                        response = jira.session.put(update_url, json=update_data)
                        if not response.ok:
                            logger.error(f"Jira PUT error updating Story Points for {issue_key}: {response.status_code} {response.text} | Payload: {update_data}")
                        else:
                            logger.info(f"Updated Story Points for {issue_key} using {correct_sp_field}")
                    else:
                        logger.warning(f"Story Points field {correct_sp_field} not editable for {issue_key} (issue type: {issue_type})")
                else:
                    logger.warning(f"Could not check editable fields for {issue_key}")
            except Exception as e:
                logger.warning(f"Could not update Story Points for {issue_key}: {e}")
        # 2. Original Estimate (timetracking) - Always attempt for all issue types, including sub-tasks
        original_estimate = row.get("Original Estimate")
        if original_estimate and str(original_estimate).strip() != "":
            try:
                # Check if timetracking is editable for this issue type
                editmeta_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}/editmeta"
                editmeta_response = jira.session.get(editmeta_url)
                if editmeta_response.ok:
                    editable_fields = editmeta_response.json().get('fields', {})
                    # Try different time tracking field approaches
                    time_fields_to_try = [
                        ('timetracking', {"fields": {"timetracking": {"originalEstimate": str(original_estimate).strip()}}}),
                        ('timeoriginalestimate', {"fields": {"timeoriginalestimate": str(original_estimate).strip()}})
                    ]
                    updated = False
                    for field_name, update_data in time_fields_to_try:
                        if field_name in editable_fields:
                            update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                            response = jira.session.put(update_url, json=update_data)
                            if response.ok:
                                logger.info(f"Updated Original Estimate for {issue_key} using {field_name}")
                                updated = True
                                break
                            else:
                                logger.debug(f"Failed to update Original Estimate using {field_name}: {response.status_code}")
                    if not updated:
                        logger.info(f"Original Estimate not supported for {issue_key} (issue type: {issue_type})")
                else:
                    logger.warning(f"Could not check editable fields for Original Estimate on {issue_key}")
            except Exception as e:
                logger.warning(f"Could not update Original Estimate for {issue_key}: {e}")
        # 3. Start Date (custom field, must match YYYY-MM-DD)
        start_date = row.get("Start Date")
        start_date_field = os.environ.get('JIRA_START_DATE_FIELD', 'customfield_10257')
        if field_mapping and isinstance(field_mapping, dict):
            start_date_field = field_mapping.get('Start Date', start_date_field)
        if start_date and re.match(r"^\d{4}-\d{2}-\d{2}$", str(start_date).strip()):
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                update_data = {"fields": {start_date_field: str(start_date).strip()}}
                response = jira.session.put(update_url, json=update_data)
                if not response.ok:
                    logger.error(f"Jira PUT error updating Start Date for {issue_key}: {response.status_code} {response.text} | Payload: {update_data}")
                else:
                    logger.info(f"Updated Start Date for {issue_key}")
            except Exception as e:
                logger.warning(f"Could not update Start Date for {issue_key}: {e}")
        # 4. Assignee (always update after creation)
        # --- Assignee update: always use accountId if available, fallback to name ---
        assignee_accountid = os.getenv("JIRA_ASSIGNEE_ACCOUNTID")
        if assignee_accountid:
            try:
                jira._update_assignee(issue_key, account_id=assignee_accountid)
            except Exception as e:
                logger.warning(f"Could not update assignee for {issue_key}: {e}")
        elif assignee_env:
            try:
                jira._update_assignee(issue_key, name=assignee_env)
            except Exception as e:
                logger.warning(f"Could not update assignee for {issue_key}: {e}")
        # 5. Time Spent (worklog)
        time_spent = row.get("Time spent")
        if time_spent and str(time_spent).strip() != "":
            try:
                jira.log_work(issue_key, str(time_spent).strip())
                logger.info(f"Logged work for {issue_key}")
            except Exception as e:
                logger.warning(f"Could not log work for {issue_key}: {e}")
        # 6. Parent (for Stories, if specified)
        parent_ref = (row.get("Parent") or "").strip()
        if parent_ref:
            try:
                parent_key = issue_map.get(parent_ref) or issue_map.get(parent_ref.lower())
                if not parent_key:
                    parent_issue = jira.get_issue(parent_ref)
                    parent_key = parent_issue.get("key")
                if parent_key:
                    update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                    update_data = {"fields": {"parent": {"key": parent_key}}}
                    jira.session.put(update_url, json=update_data)
                    logger.info(f"Linked parent {parent_key} to {issue_key}")
            except Exception as e:
                logger.warning(f"Could not set parent for {issue_key}: {e}")

    # === Story Points for Sub-tasks: ALWAYS ENABLED by default ===
    # By default, Story Points will be updated for ALL issue types, including sub-tasks.
    # To disable, set allow_sp_on_subtasks = False or use field mapping config.
    allow_sp_on_subtasks = True  # <--- DEFAULT: Story Points are updated for sub-tasks

    for idx, row in subtasks:
        parent_ref = (row["Parent"] or "").strip()
        # Try to find the parent by key or summary (case-insensitive)
        parent_key = issue_map.get(parent_ref) or issue_map.get(parent_ref.lower())
        if not parent_key:
            try:
                # If not found in the map, try to fetch from Jira
                parent_issue = jira.get_issue(parent_ref)
                parent_key = parent_issue.get("key")
                logger.info(f"Found existing Jira parent for sub-task '{row['Summary']}': {parent_key}")
            except Exception as e:
                logger.warning(f"Skipping sub-task '{row['Summary']}' because parent issue '{parent_ref}' is not defined in the CSV or in Jira. Error: {e}")
                continue

        sp_field = field_mapping.get('Story Points', 'customfield_10016') if field_mapping else 'customfield_10016'
        sp_value = row.get("Story Points") or row.get("Story point estimate")
        # Use project from .env if available, else from CSV
        project_val = project_id_env or row["Project"]
        # Always create the sub-task with minimal fields
        subtask = jira.create_subtask(
            project_key=project_val,
            summary=(row["Summary"] or "").strip(),
            parent_key=parent_key,
            assignee=None
        )
        subtask_key = subtask["key"]
        logger.info(f"Created sub-task: {subtask_key} under {parent_key}")
        all_rows[idx]["Created Issue ID"] = subtask_key

        # === Post-creation updates for sub-tasks ===
        # Includes status transition, Story Points, Start Date, Assignee, Time Spent, Parent

        # Transition logic for sub-tasks
        if transition_mode == "all":
            try:
                # Use resolution-aware transition for closing states
                if transition_all_status == "close_by_type":
                    jira.transition_to_done_with_resolution(subtask_key, "Done")
                else:
                    jira.transition_issue(subtask_key, transition_all_status)
            except Exception as e:
                logger.warning(f"Could not transition sub-task {subtask_key} to '{transition_all_status}': {e}")
        elif transition_mode == "prompt":
            print(f"\nSelect a status transition for sub-task {subtask_key} (default: {transition_default}):")
            print(f"  1. {transition_default} (default)")
            print("  2. In Progress")
            print("  3. Backlog")
            print("  4. Enter custom transition name")
            print("  5. Skip status transition for this sub-task")
            choice = input("Choose [1-5] or press Enter for default: ").strip()
            if choice == "2":
                transition_name = "In Progress"
            elif choice == "3":
                transition_name = "Backlog"
            elif choice == "4":
                transition_name = input("Enter custom transition name: ").strip() or transition_default
            elif choice == "5":
                transition_name = None
            else:
                transition_name = transition_default
            if transition_name:
                try:
                    # Use resolution-aware transition for closing states
                    if transition_name.lower() in ["close_by_type", "done", "closed", "complete", "resolve", "finished"]:
                        jira.transition_to_done_with_resolution(subtask_key, "Done")
                    else:
                        jira.transition_issue(subtask_key, transition_name)
                except Exception as e:
                    logger.warning(f"Could not transition sub-task {subtask_key} to '{transition_name}': {e}")
        # 1. Story Points (if allowed) - Using correct field ID
        if allow_sp_on_subtasks and sp_value is not None and str(sp_value).strip() != "":
            try:
                # Use the selected editable Story Points field
                correct_sp_field = sp_field
                # Check if the sub-task allows Story Points updates
                editmeta_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}/editmeta"
                editmeta_response = jira.session.get(editmeta_url)
                if editmeta_response.ok:
                    editable_fields = editmeta_response.json().get('fields', {})
                    if correct_sp_field in editable_fields:
                        update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                        update_data = {"fields": {correct_sp_field: float(sp_value)}}
                        response = jira.session.put(update_url, json=update_data)
                        if not response.ok:
                            logger.error(f"Jira PUT error updating Story Points for sub-task {subtask_key}: {response.status_code} {response.text} | Payload: {update_data}")
                        else:
                            logger.info(f"Updated Story Points for sub-task {subtask_key} using {correct_sp_field}")
                    else:
                        logger.info(f"Story Points field {correct_sp_field} not editable for sub-task {subtask_key} - this is normal")
                else:
                    logger.warning(f"Could not check editable fields for sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not update Story Points for sub-task {subtask_key}: {e}")
        # 2. Original Estimate - Skip for Sub-tasks (not supported in this Jira configuration)
        original_estimate = row.get("Original Estimate")
        if original_estimate and str(original_estimate).strip() != "":
            logger.info(f"Skipping Original Estimate for sub-task {subtask_key} - not supported in this Jira configuration")
        # 3. Start Date (use only Start Date field, not Actual Start)
        start_date = row.get("Start Date")
        start_date_field = os.environ.get('JIRA_START_DATE_FIELD', 'customfield_10257')
        if field_mapping and isinstance(field_mapping, dict):
            start_date_field = field_mapping.get('Start Date', start_date_field)
        if start_date and re.match(r"^\d{4}-\d{2}-\d{2}$", str(start_date).strip()):
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                update_data = {"fields": {start_date_field: str(start_date).strip()}}
                response = jira.session.put(update_url, json=update_data)
                if not response.ok:
                    logger.error(f"Jira PUT error updating Start Date for sub-task {subtask_key}: {response.status_code} {response.text} | Payload: {update_data}")
                else:
                    logger.info(f"Updated Start Date for sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not update Start Date for sub-task {subtask_key}: {e}")
        # 4. Assignee (always update after creation)
        # --- Assignee update: always use accountId if available, fallback to name ---
        assignee_accountid = os.getenv("JIRA_ASSIGNEE_ACCOUNTID")
        if assignee_accountid:
            try:
                jira._update_assignee(subtask_key, account_id=assignee_accountid)
            except Exception as e:
                logger.warning(f"Could not update assignee for sub-task {subtask_key}: {e}")
        elif assignee_env:
            try:
                jira._update_assignee(subtask_key, name=assignee_env)
            except Exception as e:
                logger.warning(f"Could not update assignee for sub-task {subtask_key}: {e}")
        # 5. Time Spent (log work only ONCE, do not update timetracking/timeSpent)
        time_spent = row.get("Time spent")
        if time_spent and str(time_spent).strip() != "":
            try:
                jira.log_work(subtask_key, str(time_spent).strip())
                logger.info(f"Logged work for sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not log work for sub-task {subtask_key}: {e}")
        # 6. Parent (for sub-tasks, if specified)
        parent_ref2 = (row.get("Parent") or "").strip()
        if parent_ref2:
            try:
                parent_key2 = issue_map.get(parent_ref2) or issue_map.get(parent_ref2.lower())
                if not parent_key2:
                    parent_issue2 = jira.get_issue(parent_ref2)
                    parent_key2 = parent_issue2.get("key")
                if parent_key2:
                    update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                    update_data = {"fields": {"parent": {"key": parent_key2}}}
                    jira.session.put(update_url, json=update_data)
                    logger.info(f"Linked parent {parent_key2} to sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not set parent for sub-task {subtask_key}: {e}")

    # Append only newly created issues to output/tracker.csv for persistent tracking
    # NOTE: The source CSV file (output.csv) is NOT modified - only tracker.csv gets the Created Issue IDs
    if all_rows and "Created Issue ID" in all_rows[0]:
        # Always use the project root's output directory for consistency
        project_root = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Only append newly created issues to tracker.csv
        # Only append rows that were initially empty but now have a Created Issue ID
        new_issues = []
        for idx, row in enumerate(all_rows):
            if idx in initially_empty_indices and row.get("Created Issue ID"):
                new_issues.append(row)
        
        if new_issues:
            tracker_path = os.path.join(output_dir, "tracker.csv")
            write_header = not os.path.isfile(tracker_path)
            
            with open(tracker_path, 'a', newline='', encoding='utf-8') as trackerfile:
                tracker_writer = csv.DictWriter(trackerfile, fieldnames=all_rows[0].keys())
                if write_header:
                    tracker_writer.writeheader()
                for row in new_issues:
                    tracker_writer.writerow(row)
            
            logger.info(f"Appended {len(new_issues)} newly created issues to {tracker_path}")
        else:
            logger.info("No new issues to append to tracker.csv")

###############################################################
# Main script entrypoint and environment setup
###############################################################
# This section sets up logging, loads environment variables, prompts for user input,
# and runs the main import workflow. All steps are commented for clarity.
if __name__ == "__main__":
    import getpass
    import subprocess
    import sys
    import logging
    try:
        # Setup logging to error.log as early as possible
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler("logs/error.log", mode='a', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        # ...existing code...
        # Place your main script logic here, e.g.:
        # import_stories_and_subtasks(...)
        # If your script uses argparse or input, ensure it's inside this try block
        pass  # ...existing code...
    except Exception as e:
        logging.error(f"Uncaught exception: {e}", exc_info=True)
        print(f"Uncaught exception: {e}. See error.log for details.")
    from pathlib import Path
    from dotenv import load_dotenv, set_key
    from pathlib import Path as SysPath

    # Load .env if present
    env_path = SysPath(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)

    print("=== Jira Import Automation ===\n")
    def prompt_env_var(var, prompt_text, secret=False, default=None):
        """
        Prompt for environment variable, save to .env if entered.
        """
        val = os.getenv(var)
        if val:
            print(f"{var} loaded from .env")
            return val
        if secret:
            val = getpass.getpass(f"{prompt_text}: ")
        else:
            val = input(f"{prompt_text}{' ['+default+']' if default else ''}: ") or default
        # Save the new value to .env
        if val:
            set_key(str(env_path), var, val)
        return val

    JIRA_URL = prompt_env_var("JIRA_URL", "Enter your Jira URL (e.g. https://your-domain.atlassian.net)")
    JIRA_EMAIL = prompt_env_var("JIRA_EMAIL", "Enter your Jira email")
    JIRA_TOKEN = prompt_env_var("JIRA_TOKEN", "Enter your Jira API token", secret=True)
    JIRA_ASSIGNEE = prompt_env_var("JIRA_ASSIGNEE", "Enter Jira assignee username or account ID (optional)", default="")
    # Only prompt for Project ID once at the beginning
    JIRA_PROJECT_ID = prompt_env_var("JIRA_PROJECT_ID", "Enter your Jira Project ID (e.g. ABC)")


    # Prompt user to choose CSV ingestion mode (new file or re-run last output)
    print("\nChoose import mode:")
    print("1. Ingest a new CSV file")
    print("2. Re-run import using last output/output.csv")
    mode_choice = input("Enter 1 or 2: ").strip()
    project_root = Path(__file__).parent
    output_csv = project_root / "output/output.csv"
    if mode_choice == "2":
        # Use output/output.csv directly
        import_path = str(output_csv)
        print(f"Re-running import using {import_path}")
    else:
        # Prompt for source CSV
        print("\nEnter the path to your Outlook CSV export (e.g. Testconv.csv):")
        while True:
            source_csv = input("CSV file path: ").strip()
            if Path(source_csv).is_file():
                break
            print("File not found. Please enter a valid file path.")
        # Download all Jira fields to a JSON file for debugging field issues
        print("\nFetching Jira field metadata and saving to jira_fields.json...")
        curl_cmd = [
            "curl",
            "-u", f"{JIRA_EMAIL}:{JIRA_TOKEN}",
            "-X", "GET",
            f"{JIRA_URL.rstrip('/')}/rest/api/3/field",
            "-H", "Accept: application/json",
            "-o", "jira_fields.json"
        ]
        try:
            subprocess.run(curl_cmd, check=True)
            print("Jira field metadata saved to jira_fields.json.\n")
        except subprocess.CalledProcessError as e:
            print("Warning: Could not fetch Jira field metadata. Continuing anyway.")
        # Run Outlook prep script to generate output/output.csv in output folder
        print("\nProcessing CSV for Jira import...")
        prep_script = Path(__file__).parent / "Tools" / "Outlook prep.py"
        try:
            subprocess.run([
                sys.executable, str(prep_script), source_csv
            ], check=True)
            print("CSV processing complete.\n")
        except subprocess.CalledProcessError as e:
            print("Error running Outlook prep script:")
            sys.exit(1)
        # Pause and prompt user to check output/output.csv
        print("=== Review Output ===")
        print(f"The processed file is ready at: {output_csv}")
        print("Please open and review 'output/output.csv' for accuracy and errors before proceeding.")
        proceed = input("\nType 'yes' to continue importing into Jira, or anything else to abort: ").strip().lower()
        if proceed != 'yes':
            print("Aborted. No changes made to Jira.")
            sys.exit(0)
        import_path = str(output_csv)

    # === FIELD MAPPING REVIEW ===
    # Optionally review and update custom field mapping before import
    field_mapping = {
        'Story Points': 'customfield_10146',  # Corrected to use the editable field
        'Start Date': 'customfield_10257',
        'Actual Start': 'customfield_10008',
        'Allow Story Points ': True,  # New option, default True
    }
    print("\nWould you like to review and optionally update Jira custom field mappings? (Recommended if you see field errors)")
    print("1. Yes, review and update field mapping\n2. No, use current mapping")
    field_check_choice = input("Enter 1 or 2: ").strip()
    if field_check_choice == "1":
        # Validate custom fields in field_mapping against jira_fields.json
        def validate_custom_fields(field_mapping, fields_json_path="jira_fields.json"):
            """
            Validate custom field IDs in mapping against Jira field metadata.
            """
            try:
                with open(fields_json_path, "r", encoding="utf-8") as f:
                    jira_fields = json.load(f)
                valid_field_ids = {f["id"] for f in jira_fields if f.get("custom")}
                invalid_fields = {}
                for k, v in field_mapping.items():
                    if k in ["Story Points", "Start Date", "Actual Start"] and v not in valid_field_ids:
                        invalid_fields[k] = v
                return invalid_fields
            except Exception as e:
                print(f"Warning: Could not validate custom fields: {e}")
                return {}

        # Run validation and warn user if any custom fields are invalid
        invalid_fields = validate_custom_fields(field_mapping)
        if invalid_fields:
            print("\nWARNING: The following custom fields in your mapping are NOT present in Jira:")
            for k, v in invalid_fields.items():
                print(f"  {k}: {v}")
            print("Please fix these field IDs in your mapping before continuing.")
            print("You can update them now, or abort and fix jira_fields.json/mapping.")
            print("Refer to jira_fields.json for valid custom field IDs.")
            print("\nField mapping before fix:")
            print(json.dumps(field_mapping, indent=2))
            for k in invalid_fields:
                new_id = input(f"Enter valid custom field ID for '{k}' (or leave blank to skip): ").strip()
                if new_id:
                    field_mapping[k] = new_id
            print("\nUpdated field mapping:")
            print(json.dumps(field_mapping, indent=2))
            confirm = input("Type 'yes' to continue with updated mapping, or anything else to abort: ").strip().lower()
            if confirm != "yes":
                print("Aborted. Please fix your field mapping and try again.")
                sys.exit(1)

        # Prompt user for Story Points on Sub-tasks before launching field_check.py
        print("\nDo you want to Allow Story Points ?")
        print("1. Yes (recommended)")
        print("2. No")
        sp_subtasks_choice = input("Enter 1 or 2: ").strip()
        if sp_subtasks_choice == "2":
            field_mapping['Allow Story Points '] = False
        else:
            field_mapping['Allow Story Points '] = True

        # Use a temp file to communicate mapping to field_check.py
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf_path = tf.name
            # Write current mapping including the new option
            json.dump(field_mapping, tf, indent=2)
            tf.flush()
        subprocess.run([sys.executable, "Tools/field_check.py", tf_path])
        try:
            with open(tf_path, "r", encoding="utf-8") as f:
                field_mapping = json.load(f)
            # Ensure the new option is present (default to True if missing)
            if 'Allow Story Points ' not in field_mapping:
                field_mapping['Allow Story Points '] = True
            print(f"Using field mapping: {field_mapping}")
        except Exception:
            print("Warning: Could not parse updated field mapping. Using defaults.")
    else:
        print(f"Using default field mapping: {field_mapping}")
    # Do NOT prompt for JIRA_PROJECT_ID again after field mapping review; use the value already loaded above.

    # Set env vars for this process
    os.environ["JIRA_URL"] = JIRA_URL
    os.environ["JIRA_EMAIL"] = JIRA_EMAIL
    os.environ["JIRA_TOKEN"] = JIRA_TOKEN
    if JIRA_ASSIGNEE:
        os.environ["JIRA_ASSIGNEE"] = JIRA_ASSIGNEE

    # Proceed with import using final mapping and environment
    load_dotenv(override=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("error.log", mode="a", encoding="utf-8")
        ]
    )
    jira = JiraAPI(JIRA_URL, JIRA_EMAIL, JIRA_TOKEN)
    try:
        import_stories_and_subtasks(import_path, jira, field_mapping=field_mapping)
    except Exception as e:
        logging.getLogger("JiraImport").error(f"Error: {e}")
