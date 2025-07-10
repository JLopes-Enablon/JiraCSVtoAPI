
---

# JiraCSVviaAPI-1 (V1.24)

A robust, interactive Python workflow to process Outlook calendar CSV exports for Jira import.

## Features
- **Automated CSV Cleaning & Reformatting:**
  - Cleans and normalizes Outlook CSVs for Jira import.
  - Excludes cancelled/out-of-office events.
  - Calculates Story Points from event durations.
- **Interactive User Prompts:**
  - Prompts for Jira Project ID, Issue Type, and Parent ID during CSV prep.
  - Auto-populates fields as needed.
- **Output & Idempotency:**
  - Always generates `output.csv` in the project root.
  - Only processes rows without a `Created Issue ID` (idempotent import).
  - Appends all processed rows to `tracker.csv` for persistent tracking.
- **Jira Import Automation:**
  - Imports Epics, Stories, Tasks, and Sub-tasks from CSV.
  - Handles correct parent/epic linkage for stories and sub-tasks.
  - Supports any top-level Jira issue type.
  - Maps and updates date fields (Start Date, Actual Start) in Jira issues.
  - Sends Story Points as a number (float) to Jira.
  - Handles Original Estimate and Time Spent fields, using the Jira Worklog API for time tracking.
  - Updates fields post-creation (e.g., Story Points, Original Estimate, Actual Start Date, Assignee) using additional API calls for accuracy.
  - Sub-task parent lookup supports both Jira key and summary (case-insensitive), with fallback to Jira API if not found in the CSV.
  - Uses `.env` variables for configuration, set interactively if missing.
  - All main Jira operations are encapsulated in the `JiraAPI` class, which provides methods for issue creation, sub-task creation, work logging, and error handling.
  - The script is idempotent: it updates the CSV with created issue IDs and persists all processed rows in `tracker.csv` for auditability.
  - Supports logging work (time spent) on issues and sub-tasks via the Jira Worklog API.
  - Provides robust error handling and logging for all API interactions.
  - Logs all Jira API requests and responses for troubleshooting.
- **.env Integration:**
  - Loads sensitive variables from `.env` and prompts for missing ones, saving them for future runs.
- **Robust Logging & Error Handling:**
  - All logging output is written to both console and `error.log`.
  - Logs API errors, skipped sub-tasks, and all outgoing payloads.
- **Jira Field Metadata:**
  - Fetches all Jira field metadata and saves to `jira_fields.json` before import for debugging and mapping.

## Getting Started
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the workflow:**
   ```bash
   python jiraapi.py
   ```
   - Follow the interactive prompts for credentials, CSV path, and field choices.
   - Review `output.csv` when prompted, then confirm to proceed with import.

3. **CSV Format:**
   Your CSV should have these columns:
   ```csv

   Project,Summary,IssueType,Parent,Start Date,Story Points,Original Estimate,Time spent,Priority,Created Issue ID
   ```
   - The script will prompt for missing/required fields during prep.
   - For sub-tasks, set `Parent` to the Jira key (e.g., `PROJ-123`) or summary of the parent story.
   - Only rows without a `Created Issue ID` will be imported.

## Files
- `jiraapi.py` — Main workflow, interactive, idempotent, logs API calls, .env integration, time tracking and worklog enabled.
-   - Contains the `JiraAPI` class with methods:
      - `get_issue(issue_key)`: Retrieve a Jira issue by key.
      - `create_issue(...)`: Create a new Jira issue with support for custom fields, story points, estimates, and assignee.
      - `create_subtask(...)`: Create a sub-task under a parent issue, with parent lookup by key or summary.
      - `log_work(issue_key, time_spent, comment)`: Log work (time spent) on an issue or sub-task.
      - All methods include robust error handling and logging.
- `Outlook Prep/Outlook prep.py` — CSV prep script, interactive, well-commented.
- `requirements.txt` — Python dependencies (`requests`, `python-dotenv`).
- `output.csv` — Output file, always in project root, includes Created Issue ID.
- `tracker.csv` — Persistent log of all imported issues.
- `jira_fields.json` — Auto-fetched Jira field metadata.
- `error.log` — All logging output.
- `.env` — Auto-updated with sensitive variables (created on first run).

## Logging & Troubleshooting
- All actions, API requests, and errors are logged to both console and `error.log`.
- Worklog (Time Spent) API calls are logged with full request/response details.
- If you encounter issues, check `error.log` for details.

## Environment Variables
- The following variables are required and will be prompted for if missing:
  - `JIRA_URL`: Your Jira instance URL (e.g., https://your-domain.atlassian.net)
  - `JIRA_EMAIL`: Your Jira user email
  - `JIRA_TOKEN`: Your Jira API token
  - `JIRA_ASSIGNEE`: (Optional) Default assignee username or account ID
- All variables are stored in `.env` for future runs.

### How to Obtain Required Environment Variables from Jira

- **JIRA_URL**: This is the base URL of your Jira Cloud instance. You can find it in your browser's address bar when logged into Jira (e.g., `https://your-domain.atlassian.net`).

- **JIRA_EMAIL**: Use the email address associated with your Jira account (the one you use to log in).

- **JIRA_TOKEN**: This is a personal API token, not your password. To generate one:
  1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens).
  2. Click **Create API token**.
  3. Give it a label (e.g., "JiraCSVtoAPI") and click **Create**.
  4. Copy the generated token and use it when prompted by the script.
  5. For more details, see [Atlassian's API token documentation](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).

- **JIRA_ASSIGNEE** (optional): This can be either the Jira username or the account ID of the user to assign issues to by default.
  - For Jira Cloud, account IDs are recommended. To find an account ID:
    1. Go to **Jira Settings > User Management > Users**.
    2. Click on the user and look for the account ID in the URL (e.g., `.../users/view?accountId=abc123...`).
    3. Alternatively, use the [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/#api-rest-api-3-user-search-get) to search for users and get their accountId.

All variables will be saved to your `.env` file after the first run for convenience and security.

## Advanced Details
- The script updates certain fields (e.g., Story Points, Original Estimate, Actual Start Date, Assignee) after issue creation to ensure compatibility with Jira field requirements.
- Sub-task parent lookup is robust: it matches by key or summary (case-insensitive) and will attempt to fetch the parent from Jira if not found in the CSV.
- The script is designed to be idempotent and safe for repeated runs: only rows without a `Created Issue ID` are processed, and all processed rows are appended to `tracker.csv` for persistent tracking.
- All main Jira operations are encapsulated in the `JiraAPI` class for maintainability and reuse.

## Security
- Credentials and sensitive variables are loaded from `.env` and only prompted for if missing.
- `.env` is updated automatically and should be kept secure.

## Version
- **V1.24** — All features above are active and working as of this version.

---
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability and error handling.*
