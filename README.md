
# JiraCSVviaAPI-1 — Stable Release v1.30

**Bulk import Outlook calendar events into Jira Cloud with robust field mapping, idempotent import, and full logging.**

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
   - The script will automatically rename `Subject` to `Summary` and add all required Jira columns during processing.
   - The script will prompt for missing/required fields during prep.
   - For sub-tasks, set `Parent` to the Jira key (e.g., `PROJ-123`) or summary of the parent story.
   - Only rows without a `Created Issue ID` will be imported.

---

## Features & Workflow

**1. CSV Preparation & Input**
   - Robust normalization, header mapping, and exclusion logic for Outlook exports.
   - Interactive prompts for required fields and CSV path.
   - Automatic renaming of `Subject` to `Summary` and addition of required Jira columns.

**2. Jira Field Metadata Fetch**
   - Fetches Jira field metadata (`jira_fields.json`) before import for field mapping and debugging.

**3. .env Variable Management**
   - Interactive prompts for Jira fields and .env variables, with persistent saving.
   - Project ID is a persistent .env variable and never double-prompts.

**4. Field Mapping Review**
   - Interactive utility to review and update Jira custom field mappings before import.

**5. Idempotent Import**
   - Only new rows (without Created Issue ID) are processed, ensuring safe re-runs.

**6. Resolution Status Management & Autoclose**
   - At the start of import, choose how to set the Resolution/Status for all created issues and sub-tasks:
     - **Prompt for each issue:** Closed (default), In Progress, Backlog, or custom transition per issue.
     - **All issues auto-transitioned:** Closed All, In Progress All, or Backlog All (no further prompts).
   - The "All" options apply the selected status to all issues and sub-tasks without further prompts.

**7. Jira API Integration**
   - Imports Epics, Stories, Tasks, and Sub-tasks from CSV.
   - Handles parent/epic linkage for stories and sub-tasks.
   - Updates Story Points, assignee, Start Date, Time Spent, and Parent after creation for all issue types (including sub-tasks).
   - Sub-task logic robustly supports Story Points and time tracking (with clear toggles).

**8. Logging & Tracking**
   - Persistent logging to `tracker.csv` and `error.log`.
   - All API interactions, payloads, and errors are logged for full traceability and troubleshooting.
   - All outgoing payloads and responses are logged for debugging.

**9. Workflow Flexibility**
   - Supports advanced and basic workflows.
   - .gitignore rules to exclude generated/log files.

---


---

## Story Points on Sub-tasks

By default, Story Points are updated for ALL issue types, including sub-tasks. To turn OFF Story Points for sub-tasks:

1. Open `jiraapi.py` and find:

   ```python
   allow_sp_on_subtasks = True  # <--- DEFAULT: Story Points are updated for sub-tasks
   # To turn OFF Story Points for sub-tasks, change the above line to:
   # allow_sp_on_subtasks = False
   ```
2. Change `allow_sp_on_subtasks = True` to `allow_sp_on_subtasks = False` and save the file.

You can also control this via the field mapping review utility by setting the `Allow Story Points on Sub-tasks` option when prompted.

---



## Scripts Overview & Usage

### `jiraapi.py` — Main Import & Workflow
- **Purpose:** Bulk import Outlook calendar events into Jira Cloud, with robust field mapping, idempotent import, and full logging.
- **Usage:**
  ```bash
  python jiraapi.py
  ```
- **Input:** Outlook CSV export (see above for format), interactive prompts for credentials and field mapping.
- **Output:** `output.csv` (import results), `tracker.csv` (log), `error.log` (errors).
- **Features:**
  - Interactive prompts for credentials, CSV path, and field choices.
  - Field mapping review utility.
  - Idempotent import (only new rows processed).
  - Status transition options (Closed, In Progress, Backlog, etc.).
  - Updates Story Points, assignee, Start Date, Time Spent, Parent, etc.
  - Full logging and error handling.

### `jira_update_fields.py` — Update Existing Issues from CSV
- **Purpose:** Update missing or changed fields (including custom fields) for existing Jira issues listed in a CSV/output file.
- **Usage:**
  ```bash
  python jira_update_fields.py output.csv
  ```
- **Input:** CSV file with Jira issue keys and fields to update (e.g., `output.csv`).
- **Output:** Updates issues in Jira, logs to `error.log`.
- **Features:**
  - Compares all fields in CSV to Jira and updates any that have changed.
  - Handles custom fields, time tracking, status, etc.
  - Logs work (Time Spent) for each issue.
  - Prints update summary for each row.

### `jira_export_my_issues.py` — Export All My Issues to CSV
- **Purpose:** Export all Jira issues assigned to or created by the current user to a local CSV, including all available fields.
- **Usage:**
  ```bash
  python jira_export_my_issues.py my_issues.csv
  ```
- **Input:** None (fetches from Jira using API and your credentials).
- **Output:** CSV file (`my_issues.csv`) with all fields as columns for easy editing.
- **Features:**
  - Authenticates using `.env` variables.
  - Fetches all issues assigned to or reported by you.
  - Dynamically extracts all available fields (standard + custom).
  - Writes a CSV with all fields as columns.

### `jira_field_names_export.py` — Export Field Metadata to CSV
- **Purpose:** Export all Jira field metadata (ID, display name, description) to a CSV for mapping and review.
- **Usage:**
  ```bash
  python jira_field_names_export.py jira_field_names.csv
  ```
- **Input:** None (fetches from Jira using API and your credentials).
- **Output:** CSV file (`jira_field_names.csv`) with columns: Field ID, Display Name, Description.
- **Features:**
  - Authenticates using `.env` variables.
  - Fetches all field metadata from Jira.
  - Lets you cross-reference field keys in your data CSV with human-readable names.
  - Helps you filter/edit your main data CSV for updates.

### Other Files
- `Outlook Prep/Outlook prep.py` — CSV prep script: interactive, auto-renames headers, normalizes dates, excludes unwanted events, prompts for Jira fields, and generates output.csv. Fully commented.
- `field_check.py` — Interactive field mapping review utility, lets you review and update Jira custom field mappings before import.
- `requirements.txt` — Python dependencies (`requests`, `python-dotenv`).
- `output.csv` — Output file, always in project root, includes Created Issue ID.
- `tracker.csv` — Persistent log of all imported issues.
- `jira_fields.json` — Auto-fetched Jira field metadata for field mapping and debugging.
- `error.log` — All logging output (console + file).
- `.env` — Auto-updated with sensitive variables (created on first run).

**Logging & Troubleshooting:**
- All actions, API requests, and errors are logged to both console and `error.log` for persistent troubleshooting.
- Worklog (Time Spent) API calls are logged with full request/response details.
- All outgoing payloads and responses are logged for debugging.
- If you encounter issues, check `error.log` for details.

**Security:**
- Credentials and sensitive variables are loaded from `.env` and only prompted for if missing.
- `.env` is updated automatically and should be kept secure.
- Assignee logic supports Jira Cloud accountId for compatibility.

---

## Version

- **V1.30 (Stable)** — Resolution Status Management expanded: Now supports 6 options (Closed, In Progress, Backlog, Closed All, In Progress All, Backlog All) for status/transition selection. The "All" options apply the selected status to all issues and sub-tasks without further prompts. All other features from v1.29 retained. This is a stable release.

---

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

## Version
- **V1.30 (Stable)** — Resolution Status Management expanded: Now supports 6 options (Done, In Progress, Backlog, Done All, In Progress All, Backlog All) for status/transition selection. The "All" options apply the selected status to all issues and sub-tasks without further prompts. All other features from v1.29 retained. This is a stable release.

---
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability, error handling, and a fully maintainable, production-ready codebase.*
