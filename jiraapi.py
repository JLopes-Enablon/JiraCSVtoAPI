
import requests
import os
import csv
import logging
import re
from dotenv import load_dotenv
from typing import Any, Dict, Optional

class JiraAPI:
    """
    A class to interact with the Jira REST API.
    Handles authentication, issue creation, sub-task creation, and error handling.
    """
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """
        Initialize the JiraAPI client and set up logging.
        """
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

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Story", story_points: Optional[Any] = None, original_estimate: Optional[Any] = None, time_spent: Optional[Any] = None, start_date: Optional[str] = None, assignee: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
        """
        Create a new Jira issue.
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the issue.
            issue_type: The type of issue (default: 'Story').
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
        # Only set fields that are safe to set on create
        fields_dict.update(fields)
        data = {"fields": fields_dict}
        self.logger.info(f"Creating issue in project {project_key} with summary '{summary}'")
        self.logger.debug(f"Payload for issue creation: {data}")
        response = self.session.post(url, json=data)
        self._handle_response(response)
        issue_key = response.json().get("key", "<unknown>")
        self.logger.info(f"Created issue: {issue_key} in project {project_key}")


        # Post-creation field updates (Actual start, Story Points, Original Estimate, Assignee)
        # 1. Actual start date (customfield_10008)
        actual_start_date = None
        if start_date:
            date_str = str(start_date).strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                actual_start_date = date_str
            else:
                self.logger.warning(f"Start Date '{start_date}' is not in 'YYYY-MM-DD' format. Not updating Actual start date field.")
        if actual_start_date and issue_key != "<unknown>":
            update_url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            update_data = {"fields": {"customfield_10008": actual_start_date}}
            self.logger.info(f"Updating Actual start date for {issue_key} to {actual_start_date}")
            self.logger.debug(f"Payload for Actual start update: {update_data}")
            update_response = self.session.put(update_url, json=update_data)
            self._handle_response(update_response)
            self.logger.info(f"Updated Actual start date for {issue_key}")

        # 1b. Always update assignee after creation (guaranteed assignment)
        assignee_accountid = os.getenv("JIRA_ASSIGNEE_ACCOUNTID")
        if issue_key != "<unknown>":
            if assignee_accountid:
                self._update_assignee(issue_key, account_id=assignee_accountid)
            elif assignee:
                self._update_assignee(issue_key, name=assignee)

        # 2. Story Points (customfield_10037) and Original Estimate (timetracking)
        update_fields = {}
        # Convert story_points to a number if possible, else skip
        sp_value = None
        if story_points is not None and str(story_points).strip() != "":
            try:
                sp_value = float(story_points)
            except Exception:
                self.logger.warning(f"Story Points value '{story_points}' is not a valid number. Skipping.")
        if sp_value is not None:
            update_fields["customfield_10037"] = sp_value
        if original_estimate:
            update_fields["timetracking"] = {"originalEstimate": original_estimate}
        if update_fields and issue_key != "<unknown>":
            update_url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            update_data = {"fields": update_fields}
            self.logger.info(f"Updating Story Points/Original Estimate for {issue_key}")
            self.logger.debug(f"Payload for Story Points/Original Estimate update: {update_data}")
            update_response = self.session.put(update_url, json=update_data)
            self._handle_response(update_response)
            self.logger.info(f"Updated Story Points/Original Estimate for {issue_key}")

        # 3. Log work (Time Spent) if provided and valid
        ts_value = None
        if time_spent is not None and str(time_spent).strip() != "":
            ts_value = str(time_spent).strip()
        if ts_value and issue_key != "<unknown>":
            self.log_work(issue_key, ts_value)

        return response.json()

    def _update_assignee(self, issue_key: str, account_id: Optional[str] = None, name: Optional[str] = None) -> None:
        """
        Helper to update the assignee of an issue by accountId or name.
        """
        update_url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        if account_id:
            update_data = {"fields": {"assignee": {"id": account_id}}}
            self.logger.info(f"Updating assignee for {issue_key} to accountId {account_id}")
        elif name:
            update_data = {"fields": {"assignee": {"name": name}}}
            self.logger.info(f"Updating assignee for {issue_key} to {name}")
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
        start_date: Optional[str] = None,
        # story_points and timetracking fields are ignored for sub-tasks by default
        story_points: Optional[Any] = None,
        original_estimate: Optional[Any] = None,
        time_spent: Optional[Any] = None,
        priority: Optional[str] = None,
        **fields: Any
    ) -> Dict[str, Any]:
        """
        Create a Jira sub-task under a parent issue.
        Args:
            project_key: The Jira project key.
            summary: The summary/title of the sub-task.
            parent_key: The key of the parent story.
            assignee: (Optional) Assignee username.
            start_date: (Optional) Start date for the sub-task.
            story_points: (Optional) Story points value.
            original_estimate: (Optional) Original time estimate.
            time_spent: (Optional) Time spent value.
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
        # Do NOT set customfield_10015 (Start Date) for sub-tasks unless it is on the sub-task create screen in Jira
        # if start_date and <your condition for sub-tasks>:
        #     subtask_fields["customfield_10015"] = start_date
        # Enable timetracking fields for sub-tasks if provided (but NOT timeSpent)
        if original_estimate:
            subtask_fields["timetracking"] = {"originalEstimate": original_estimate}
        if priority:
            subtask_fields["priority"] = {"name": priority}
        subtask_fields.update(fields)
        data = {"fields": subtask_fields}
        self.logger.debug(f"Creating sub-task under parent {parent_key} in project {project_key} with summary '{summary}'")
        response = self.session.post(url, json=data)
        self._handle_response(response)
        subtask_key = response.json().get("key", "<unknown>")
        self.logger.info(f"Created sub-task: {subtask_key} under parent {parent_key}")

        # Update Actual start date (customfield_10008) for sub-tasks after creation, if start_date is valid
        actual_start_date = None
        if start_date:
            import re
            date_str = str(start_date).strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                actual_start_date = date_str
            else:
                self.logger.warning(f"Start Date '{start_date}' is not in 'YYYY-MM-DD' format. Not updating Actual start date field.")
        if actual_start_date and subtask_key != "<unknown>":
            update_url = f"{self.base_url}/rest/api/3/issue/{subtask_key}"
            update_data = {"fields": {"customfield_10008": actual_start_date}}
            self.logger.info(f"Updating Actual start date for {subtask_key} to {actual_start_date}")
            self.logger.debug(f"Payload for Actual start update: {update_data}")
            update_response = self.session.put(update_url, json=update_data)
            self._handle_response(update_response)
            self.logger.info(f"Updated Actual start date for {subtask_key}")

        # Log work (Time Spent) if provided and valid
        ts_value = None
        if time_spent is not None and str(time_spent).strip() != "":
            ts_value = str(time_spent).strip()
        if ts_value and subtask_key != "<unknown>":
            self.log_work(subtask_key, ts_value)

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



def import_stories_and_subtasks(csv_path: str, jira: JiraAPI) -> None:
    """
    Import stories and sub-tasks from a CSV file into Jira.
    Expects CSV with columns: Project, Summary, IssueType, Parent, Start Date, Story Points, Original Estimate, Time spent, Priority.
    Assignee is read from the environment variable JIRA_ASSIGNEE.
    Trims whitespace and matches parent stories case-insensitively.
    Only creates sub-tasks if their parent story is defined in the CSV.
    Args:
        csv_path: Path to the CSV file.
        jira: JiraAPI instance.
    """
    logger = logging.getLogger("JiraImport")
    assignee_env = os.getenv("JIRA_ASSIGNEE")

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

    # Create all top-level issues (Story, Task, etc.)
    for idx, row in top_level_issues:
        summary_clean = (row["Summary"] or "").strip()
        issue_type = (row.get("IssueType") or "Story").strip()
        # Create the issue in Jira, now passing story_points and original_estimate
        issue = jira.create_issue(
            project_key=row["Project"],
            summary=summary_clean,
            issue_type=issue_type,
            start_date=row.get("Start Date"),
            story_points=row.get("Story Points"),
            original_estimate=row.get("Original Estimate"),
            time_spent=row.get("Time spent"),
            assignee=assignee_env
        )
        issue_key = issue["key"]
        # Add the new issue to the map for parent lookup
        issue_map[issue_key] = issue_key
        issue_map[summary_clean.lower()] = issue_key
        logger.info(f"Created {issue_type}: {issue_key}")
        all_rows[idx]["Created Issue ID"] = issue_key

    # Create all sub-tasks, linking to their parent issues
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
        # Create the sub-task in Jira
        subtask = jira.create_subtask(
            project_key=row["Project"],
            summary=(row["Summary"] or "").strip(),
            parent_key=parent_key,
            assignee=assignee_env,
            start_date=row.get("Start Date"),
            story_points=row.get("Story Points"),
            original_estimate=row.get("Original Estimate"),
            time_spent=row.get("Time spent"),
            priority=row.get("Priority")
        )
        logger.info(f"Created sub-task: {subtask['key']} under {parent_key}")
        all_rows[idx]["Created Issue ID"] = subtask["key"]

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
        import_stories_and_subtasks(str(output_csv), jira)
    except Exception as e:
        logging.getLogger("JiraImport").error(f"Error: {e}")
