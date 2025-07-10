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

class JiraAPI:

    def transition_issue(self, issue_key: str, transition_name: str = "Done") -> None:
        """
        Transition a Jira issue to a new status by name (e.g., Done, In Progress, Backlog).
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123').
            transition_name: The name of the transition to perform (default: 'Done').
        Raises:
            Exception: If the transition fails or is not found.
        """
        # Get available transitions
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = self.session.get(url)
        self._handle_response(resp)
        transitions = resp.json().get("transitions", [])
        # Find the transition by name (case-insensitive)
        transition = next((t for t in transitions if t["name"].lower() == transition_name.lower()), None)
        if not transition:
            available = ", ".join([t["name"] for t in transitions])
            raise Exception(f"Transition '{transition_name}' not found for {issue_key}. Available: {available}")
        transition_id = transition["id"]
        # Perform the transition
        post_url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        data = {"transition": {"id": transition_id}}
        post_resp = self.session.post(post_url, json=data)
        self._handle_response(post_resp)
        self.logger.info(f"Transitioned {issue_key} to '{transition_name}'")
    """
    A class to interact with the Jira REST API.
    Handles authentication, issue creation, sub-task creation, and error handling.
    """
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """
        Initialize the JiraAPI client.
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
        Retrieve a Jira issue by its key.
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

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Story", assignee: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
        """
        Create a new Jira issue with only safe fields (custom fields are handled post-creation).
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the issue.
            issue_type: The type of issue (default: 'Story').
            assignee: (Optional) Assignee username (for legacy Jira only).
            **fields: Additional fields for the issue.
        Returns:
            The created issue data as a dictionary.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        fields_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if assignee:
            fields_dict["assignee"] = {"name": assignee}
        # Only set fields that are safe to set on create (exclude custom fields like Story Points)
        safe_fields = {k: v for k, v in fields.items() if not k.startswith('customfield_')}
        fields_dict.update(safe_fields)
        data = {"fields": fields_dict}
        self.logger.info(f"Creating issue in project {project_key} with summary '{summary}'")
        self.logger.debug(f"Payload for issue creation: {data}")
        response = self.session.post(url, json=data)
        self._handle_response(response)
        issue_key = response.json().get("key", "<unknown>")
        self.logger.info(f"Created issue: {issue_key} in project {project_key}")
        return response.json()

    def _update_assignee(self, issue_key: str, account_id: Optional[str] = None, name: Optional[str] = None) -> None:
        """
        Helper to update the assignee of an issue by accountId (Jira Cloud) or name (Jira Server/DC).
        Always uses 'id' if the value looks like an accountId (contains a colon or is a UUID).
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
        Create a Jira sub-task under a parent issue. Only safe fields are set on creation.
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the sub-task.
            parent_key: The key of the parent story.
            assignee: (Optional) Assignee username (for legacy Jira only).
            priority: (Optional) Priority name.
            **fields: Additional fields for the sub-task.
        Returns:
            The created sub-task data as a dictionary.
        Raises:
            Exception: If the API call fails.
        """
        url = f"{self.base_url}/rest/api/3/issue"
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
        # Only set safe fields (exclude custom fields)
        safe_fields = {k: v for k, v in fields.items() if not k.startswith('customfield_')}
        subtask_fields.update(safe_fields)
        data = {"fields": subtask_fields}
        self.logger.debug(f"Creating sub-task under parent {parent_key} in project {project_key} with summary '{summary}'")
        response = self.session.post(url, json=data)
        self._handle_response(response)
        subtask_key = response.json().get("key", "<unknown>")
        self.logger.info(f"Created sub-task: {subtask_key} under parent {parent_key}")
        return response.json()

    def _handle_response(self, response: requests.Response) -> None:
        """
        Handle the HTTP response from the Jira API.
        Args:
            response: The HTTP response object.
        Raises:
            Exception: If the response status is not OK.
        """
        if not response.ok:
            self.logger.error(f"Jira API error: {response.status_code} {response.text}")
            raise Exception(f"Jira API error: {response.status_code} {response.text}")

# End of JiraAPI class



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

    # Read and classify rows from the CSV file
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for idx, row in enumerate(reader):
            all_rows.append(row)
            # Only process rows that have not yet been imported (no Created Issue ID)
            if not row.get("Created Issue ID"):
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

    # Expanded transition options: 6 choices
    print("\nSelect a status transition mode for created issues:")
    print("  1. Done (default, prompt for each issue)")
    print("  2. In Progress (prompt for each issue)")
    print("  3. Backlog (prompt for each issue)")
    print("  4. Done All (all issues will be marked as Done, no further prompts)")
    print("  5. In Progress All (all issues will be marked as In Progress, no further prompts)")
    print("  6. Backlog All (all issues will be marked as Backlog, no further prompts)")
    mode_choice = input("Choose [1-6] or press Enter for default: ").strip()
    if mode_choice == "4":
        transition_mode = "all"
        transition_all_status = "Done"
        transition_default = "Done"
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
        transition_default = "Done"

    # Create all top-level issues (Story, Task, etc.)
    for idx, row in top_level_issues:
        summary_clean = (row["Summary"] or "").strip()
        issue_type = (row.get("IssueType") or "Story").strip()
        sp_field = field_mapping.get('Story Points', 'customfield_10037') if field_mapping else 'customfield_10037'
        sp_value = row.get("Story Points")
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

        # Transition logic
        if transition_mode == "all":
            try:
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
                    jira.transition_issue(issue_key, transition_name)
                except Exception as e:
                    logger.warning(f"Could not transition {issue_key} to '{transition_name}': {e}")
        # 1. Story Points (for all issue types and sub-tasks if allowed)
        allow_update_sp = True
        if issue_type.lower() == "sub-task" and field_mapping and isinstance(field_mapping, dict):
            allow_update_sp = field_mapping.get('Allow Story Points on Sub-tasks', False)
        if allow_update_sp and sp_field and sp_value is not None and str(sp_value).strip() != "":
            try:
                with open("jira_fields.json", "r", encoding="utf-8") as f:
                    fields_json = json.load(f)
                if any(f['id'] == sp_field for f in fields_json):
                    update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                    update_data = {"fields": {sp_field: float(sp_value)}}
                    jira.session.put(update_url, json=update_data)
                    logger.info(f"Updated Story Points for {issue_key}")
            except Exception as e:
                logger.warning(f"Could not update Story Points for {issue_key}: {e}")
        # 2. Original Estimate (timetracking)
        original_estimate = row.get("Original Estimate")
        if original_estimate and str(original_estimate).strip() != "":
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                update_data = {"fields": {"timetracking": {"originalEstimate": str(original_estimate).strip()}}}
                jira.session.put(update_url, json=update_data)
                logger.info(f"Updated Original Estimate for {issue_key}")
            except Exception as e:
                logger.warning(f"Could not update Original Estimate for {issue_key}: {e}")
        # 3. Start Date
        start_date = row.get("Start Date")
        start_date_field = os.environ.get('JIRA_START_DATE_FIELD', 'customfield_10015')
        if field_mapping and isinstance(field_mapping, dict):
            start_date_field = field_mapping.get('Start Date', start_date_field)
        if start_date and re.match(r"^\d{4}-\d{2}-\d{2}$", str(start_date).strip()):
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{issue_key}"
                update_data = {"fields": {start_date_field: str(start_date).strip()}}
                jira.session.put(update_url, json=update_data)
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
        # 5. Time Spent
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
    #
    # To disable Story Points for sub-tasks, set the following variable to False.
    #
    #    allow_sp_on_subtasks = False
    #
    # Or, to control this via the field mapping config (advanced):
    #    if field_mapping and isinstance(field_mapping, dict):
    #        allow_sp_on_subtasks = field_mapping.get('Allow Story Points on Sub-tasks', True)
    #
    # If you want to expose this as a user option, see the README for instructions.
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

        sp_field = field_mapping.get('Story Points', 'customfield_10037') if field_mapping else 'customfield_10037'
        sp_value = row.get("Story Points")
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

        # Transition logic for sub-tasks
        if transition_mode == "all":
            try:
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
                    jira.transition_issue(subtask_key, transition_name)
                except Exception as e:
                    logger.warning(f"Could not transition sub-task {subtask_key} to '{transition_name}': {e}")
        # 1. Story Points (if allowed)
        if allow_sp_on_subtasks and sp_field and sp_value is not None and str(sp_value).strip() != "":
            try:
                with open("jira_fields.json", "r", encoding="utf-8") as f:
                    fields_json = json.load(f)
                if any(f['id'] == sp_field for f in fields_json):
                    update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                    update_data = {"fields": {sp_field: float(sp_value)}}
                    jira.session.put(update_url, json=update_data)
                    logger.info(f"Updated Story Points for sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not update Story Points for sub-task {subtask_key}: {e}")
        # 2. Original Estimate (timetracking, but NOT timeSpent)
        original_estimate = row.get("Original Estimate")
        if original_estimate and str(original_estimate).strip() != "":
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                update_data = {"fields": {"timetracking": {"originalEstimate": str(original_estimate).strip()}}}
                jira.session.put(update_url, json=update_data)
                logger.info(f"Updated Original Estimate for sub-task {subtask_key}")
            except Exception as e:
                logger.warning(f"Could not update Original Estimate for sub-task {subtask_key}: {e}")
        # 3. Start Date (use only Start Date field, not Actual Start)
        start_date = row.get("Start Date")
        start_date_field = os.environ.get('JIRA_START_DATE_FIELD', 'customfield_10015')
        if field_mapping and isinstance(field_mapping, dict):
            start_date_field = field_mapping.get('Start Date', start_date_field)
        if start_date and re.match(r"^\d{4}-\d{2}-\d{2}$", str(start_date).strip()):
            try:
                update_url = f"{jira.base_url}/rest/api/3/issue/{subtask_key}"
                update_data = {"fields": {start_date_field: str(start_date).strip()}}
                jira.session.put(update_url, json=update_data)
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

    # Write back the Created Issue ID to output.csv
    if all_rows and "Created Issue ID" in all_rows[0]:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_rows[0].keys())
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)

        # Append all rows to tracker.csv for persistent tracking
        tracker_path = os.path.join(os.path.dirname(csv_path), "tracker.csv")
        # Check if tracker.csv exists to determine if we need to write the header
        write_header = not os.path.isfile(tracker_path)
        with open(tracker_path, 'a', newline='', encoding='utf-8') as trackerfile:
            tracker_writer = csv.DictWriter(trackerfile, fieldnames=all_rows[0].keys())
            if write_header:
                tracker_writer.writeheader()
            for row in all_rows:
                tracker_writer.writerow(row)

if __name__ == "__main__":

    import getpass
    import subprocess
    import sys
    from pathlib import Path
    from dotenv import load_dotenv, set_key
    from pathlib import Path as SysPath

    # Load .env if present
    env_path = SysPath(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path, override=True)

    print("=== Jira Import Automation ===\n")
    def prompt_env_var(var, prompt_text, secret=False, default=None):
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

    # Run Outlook prep script to generate output.csv in project root
    print("\nProcessing CSV for Jira import...")
    prep_script = Path(__file__).parent / "Outlook Prep" / "Outlook prep.py"
    project_root = Path(__file__).parent
    output_csv = project_root / "output.csv"
    try:
        # V1.22: Run Outlook Prep script interactively so user can respond to prompts
        subprocess.run([
            sys.executable, str(prep_script), source_csv
        ], check=True)
        print("CSV processing complete.\n")
    except subprocess.CalledProcessError as e:
        print("Error running Outlook prep script:")
        sys.exit(1)

    # Pause and prompt user to check output.csv
    print("=== Review Output ===")
    print(f"The processed file is ready at: {output_csv}")
    print("Please open and review 'output.csv' for accuracy and errors before proceeding.")
    proceed = input("\nType 'yes' to continue importing into Jira, or anything else to abort: ").strip().lower()
    if proceed != 'yes':
        print("Aborted. No changes made to Jira.")
        sys.exit(0)
    import_path = str(output_csv)

    # === FIELD MAPPING REVIEW ===
    field_mapping = {
        'Story Points': 'customfield_10037',
        'Actual Start': 'customfield_10008',
        'Allow Story Points on Sub-tasks': False,  # New option, default False
    }
    print("\nWould you like to review and optionally update Jira custom field mappings? (Recommended if you see field errors)")
    print("1. Yes, review and update field mapping\n2. No, use current mapping")
    field_check_choice = input("Enter 1 or 2: ").strip()
    if field_check_choice == "1":
        # Use a temp file to communicate mapping
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf_path = tf.name
            # Write current mapping including the new option
            json.dump(field_mapping, tf, indent=2)
            tf.flush()
        subprocess.run([sys.executable, "field_check.py", tf_path])
        try:
            with open(tf_path, "r", encoding="utf-8") as f:
                field_mapping = json.load(f)
            # Ensure the new option is present (default to False if missing)
            if 'Allow Story Points on Sub-tasks' not in field_mapping:
                field_mapping['Allow Story Points on Sub-tasks'] = False
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

    # Proceed with import
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
