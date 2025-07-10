# JiraCSVviaAPI-1 — Stable Release v1.28

**Bulk import Outlook calendar events into Jira Cloud with robust field mapping, idempotent import, and full logging.**

---

**Features:**
- Imports Epics, Stories, Tasks, and Sub-tasks from CSV
- Handles parent/epic linkage for stories and sub-tasks
- Robust CSV normalization, header mapping, and exclusion logic
- Interactive prompts for Jira fields and .env variables, with persistent saving
- Idempotent import (only new rows processed)
- Persistent logging to `tracker.csv` and `error.log`
- Fetches Jira field metadata (`jira_fields.json`) before import
- Supports advanced and basic workflows
- Updates Story Points, assignee, Start Date, Time Spent, and Parent after creation for all issue types (including sub-tasks)
- Project ID is a persistent .env variable
- Interactive field mapping review utility
- All API interactions and payloads are logged for troubleshooting
- .gitignore rules to exclude generated/log files
- **NEW in v1.28:**
    - All stale/legacy code fully removed from all scripts for a clean, maintainable codebase.
    - All scripts are now fully commented for clarity and maintainability.
    - README updated with all features, options, and usage instructions.
    - Project flagged as **stable** and ready for production use.
    - Story Points, assignee, Start Date, Time Spent, and Parent are always updated after creation for all issue types (including sub-tasks).
    - Project ID is a persistent .env variable and never double-prompts.
    - Sub-task logic robustly supports Story Points and time tracking (with clear toggles).
    - All API interactions, payloads, and errors are logged for full traceability.
    - This release is flagged as **stable**.

---

## Functionality Overview

This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability and error handling. Key features include:

- **CSV Preparation:** Robust normalization, header mapping, and exclusion logic for Outlook exports. Interactive prompts for required fields.
- **Field Mapping Review:** Interactive utility to review and update Jira custom field mappings before import.
- **Idempotent Import:** Only new rows (without Created Issue ID) are processed, ensuring safe re-runs.
- **Jira API Integration:** All issue types supported, with post-creation updates for Story Points, assignee, Start Date, Time Spent, and Parent.
- **Logging:** All API calls, errors, and actions are logged to both console and `error.log`.
- **.env Integration:** All sensitive variables are loaded from `.env` and only prompted for if missing.
- **Persistent Tracking:** All processed rows are appended to `tracker.csv` for auditability.
  - **NEW:** Story Points, assignee, Start Date, Time Spent, and Parent are always updated after creation for all issue types (including sub-tasks). Project ID is persistent and never double-prompts. All stale code removed and scripts fully commented.
### Story Points on Sub-tasks

**By default, Story Points are now updated for ALL issue types, including sub-tasks.**

If you want to turn OFF Story Points for sub-tasks (for compatibility with your Jira board):

1. Open `jiraapi.py` and find the following section in the `import_stories_and_subtasks` function:

    ```python
    allow_sp_on_subtasks = True  # <--- DEFAULT: Story Points are updated for sub-tasks
    # To turn OFF Story Points for sub-tasks, change the above line to:
    # allow_sp_on_subtasks = False
    ```

2. Change `allow_sp_on_subtasks = True` to `allow_sp_on_subtasks = False` and save the file.

**Advanced Option:**

If you want to control this via the field mapping review utility, you can uncomment the code in `jiraapi.py` as described in the comments, or set the `Allow Story Points on Sub-tasks` option in the field mapping review utility when prompted.

---

---

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
   Your Outlook CSV export should have these columns:
   ```csv
   Subject,Start Date,Start Time,End Time
   ```
   The script will automatically rename `Subject` to `Summary` and add all required Jira columns during processing.
   - The script will prompt for missing/required fields during prep.
   - For sub-tasks, set `Parent` to the Jira key (e.g., `PROJ-123`) or summary of the parent story.
   - Only rows without a `Created Issue ID` will be imported.

## Files
- `jiraapi.py` — Main workflow: interactive, idempotent, logs API calls, .env integration, time tracking and worklog enabled, Start Date update after creation, robust error handling, and field mapping review. All stale code removed and fully commented.
- `Outlook Prep/Outlook prep.py` — CSV prep script: interactive, auto-renames headers, normalizes dates, excludes unwanted events, prompts for Jira fields, and generates output.csv. Fully commented.
- `field_check.py` — Interactive field mapping review utility, lets you review and update Jira custom field mappings before import.
- `requirements.txt` — Python dependencies (`requests`, `python-dotenv`).
- `output.csv` — Output file, always in project root, includes Created Issue ID.
- `tracker.csv` — Persistent log of all imported issues.
- `jira_fields.json` — Auto-fetched Jira field metadata for field mapping and debugging.
- `error.log` — All logging output (console + file).
- `.env` — Auto-updated with sensitive variables (created on first run).

## Logging & Troubleshooting
- All actions, API requests, and errors are logged to both console and `error.log` for persistent troubleshooting.
- Worklog (Time Spent) API calls are logged with full request/response details.
- All outgoing payloads and responses are logged for debugging.
- If you encounter issues, check `error.log` for details.

## Security
- Credentials and sensitive variables are loaded from `.env` and only prompted for if missing.
- `.env` is updated automatically and should be kept secure.
- Assignee logic supports Jira Cloud accountId for compatibility.

## Version
- **V1.28 (Stable)** — All stale/legacy code removed, all scripts fully commented, README updated, and all features robustly supported. Story Points, assignee, Start Date, Time Spent, and Parent are always updated after creation for all issue types (including sub-tasks). Project ID is persistent and never double-prompts. This is a stable release.

## Required .env Variables & How to Obtain Them in Jira

The script will prompt for these variables on first run and save them to `.env`:

- `JIRA_URL` — Your Jira Cloud instance URL (e.g., `https://your-domain.atlassian.net`)
- `JIRA_EMAIL` — Your Jira user email (the one used to log in to Jira Cloud)
- `JIRA_TOKEN` — Your Jira API token (see below)
- `JIRA_ASSIGNEE` — (Optional) Jira username or account ID for the assignee (see below)

### How to get your Jira API token
1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Name your token and click **Create**
4. Copy the token and use it when prompted for `JIRA_TOKEN`

### How to get your Jira accountId (for assignee)
1. In Jira Cloud, go to **People** or your user profile
2. Click on the user you want to assign issues to
3. The URL will look like `.../people/712020:e78e154e-5582-4c59-9e72-0df53ed664af` — the part after `/people/` is the `accountId`
4. Use this value for `JIRA_ASSIGNEE` when prompted (or leave blank to assign manually)

### How to get your Jira Cloud URL
1. Log in to Jira in your browser
2. The URL in the address bar (e.g., `https://your-domain.atlassian.net`) is your `JIRA_URL`

The script will prompt for any missing variables and save them to `.env` for future runs.

---
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability, error handling, and a fully maintainable, production-ready codebase.*
