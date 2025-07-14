
# JiraCSVviaAPI-1 — Stable Release v1.32

**Bulk import Outlook calendar events into Jira Cloud with unified menu interface, robust field mapping, idempotent import, bulk transition capabilities, and full logging.**

---

## Getting Started

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the unified toolkit:**

   ```bash
   python main.py
   ```
   - Access all functionality through an organized menu system
   - Use numbered options (1-9) or keyboard shortcuts (I, P, U, C, E, T, W, F, R, Q)
   - Automatically returns to menu after each operation for continuous workflow

3. **Alternative: Run individual scripts:**

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

## Automated Bulk Transition Workflow

**Quick Start (Recommended):**
```bash
python main.py
# Select option 7 (or press 'W') for automated workflow
```

**Manual Step-by-Step:**

For efficiently completing large numbers of Jira issues:

1. **Export your issues:**
   ```bash
   python jira_export_my_issues.py bulk_transition_issues.csv
   # OR use main.py → option 5 (E) → option 1
   ```

2. **Review the exported issues** (optional - check issue types and current statuses)

3. **Run bulk transition with automatic detection:**
   ```bash
   python jira_bulk_transition.py bulk_transition_issues.csv
   # OR use main.py → option 6 (T)
   ```

4. **Review the results:**
   - Check console output for summary
   - Review `transition_report.csv` for detailed results
   - Handle any failed transitions manually if needed

**Smart Status Detection:**
- **Epics & Stories** → automatically transitioned to "Closed"
- **Tasks & Sub-tasks** → automatically transitioned to "Done"
- **Manual Override** available if you need all issues to go to the same status

---

## Menu-Driven Interface

The toolkit now includes a unified menu system (`main.py`) that organizes all functionality:

### **📅 Calendar Import Functions**
- **Import calendar events** (Option 1 / I) → `jiraapi.py`
- **Prepare Outlook CSV** (Option 2 / P) → `Outlook Prep/Outlook prep.py`

### **📝 Issue Updates**
- **Update existing issues** (Option 3 / U) → `jira_update_fields.py`
- **Configure field mappings** (Option 4 / C) → `field_check.py`

### **📊 Bulk Updates and Exports**
- **Export issues** (Option 5 / E) → `jira_export_my_issues.py` with submenu
- **Bulk transition** (Option 6 / T) → `jira_bulk_transition.py`
- **Complete workflow** (Option 7 / W) → Automated export → transition

### **🔧 Sundry Functions**
- **Export field metadata** (Option 8 / F) → `jira_field_names_export.py`
- **Check transitions** (Option 9 / R) → `jira_check_transitions.py`

**Features:**
- 🎯 **Keyboard shortcuts** for quick access (I, P, U, C, E, T, W, F, R, Q)
- 🔄 **Automated workflows** (Option 7 handles export → bulk transition automatically)
- 🔁 **Continuous operation** (returns to menu after each task)
- 📊 **Progress tracking** and comprehensive error handling
- 📝 **Activity logging** to `main_menu.log`

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

### `jira_export_my_issues.py` — Export Your Issues to CSV
- **Purpose:** Export all Jira issues assigned to or created by you to a local CSV with only the essential fields that match the output.csv format.
- **Usage:**
  ```bash
  python jira_export_my_issues.py my_issues.csv
  ```
- **Input:** None (fetches from Jira using API and your credentials).
- **Output:** CSV file (`my_issues.csv`) with the same column structure as output.csv for consistency.
- **Features:**
  - Authenticates using `.env` variables.
  - Fetches all issues assigned to or reported by you with pagination support.
  - Extracts only the specific fields used in output.csv: Project, Summary, IssueType, Parent, Start Date, Story Points, Original Estimate, Time spent, Priority, Created Issue ID.
  - Formats time fields consistently (e.g., "1h 30m", "45m").
  - Creates CSV ready for local editing and re-import using `jira_update_fields.py`.
  - Handles large datasets (tested with 300+ issues) with progress indicators.

### `jira_bulk_transition.py` — Bulk Status Transitions
- **Purpose:** Transition multiple Jira issues to completion status in bulk, with intelligent status detection based on issue type.
- **Usage:**
  ```bash
  # Automatic status detection (recommended)
  python jira_bulk_transition.py bulk_transition_issues.csv
  
  # Manual status override
  python jira_bulk_transition.py bulk_transition_issues.csv "Done"
  ```
- **Input:** CSV file with Jira issues (typically exported using `jira_export_my_issues.py`).
- **Output:** Detailed transition report CSV showing success/failure for each issue.
- **Features:**
  - **Smart Status Detection:** Automatically selects appropriate completion status:
    - Epic, Story → "Closed"
    - Task, Sub-task → "Done"
  - **Manual Override:** Force all issues to a specific status if needed.
  - **Progress Tracking:** Real-time progress with issue-by-issue feedback.
  - **Detailed Reporting:** Comprehensive CSV report with transition results.
  - **Error Handling:** Graceful handling of workflow restrictions and invalid transitions.
  - **Safety Features:** Confirmation prompts and dry-run capabilities.
  - **High Success Rate:** Tested with 300+ issues achieving 99.7% success rate.

### `jira_export_my_issues.py` — Export All My Issues to CSV (Full Fields)
- **Purpose:** Export all Jira issues assigned to or created by the current user to a local CSV, including all available fields.
- **Usage:**
  ```bash
  python jira_export_my_issues.py my_issues_full.csv
  ```
- **Input:** None (fetches from Jira using API and your credentials).
- **Output:** CSV file (`my_issues_full.csv`) with all fields as columns for easy editing.
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
- `main.py` — **Unified menu system**: Organized interface for all toolkit functionality with keyboard shortcuts, automated workflows, and continuous operation.
- `Outlook Prep/Outlook prep.py` — CSV prep script: interactive, auto-renames headers, normalizes dates, excludes unwanted events, prompts for Jira fields, and generates output.csv. Fully commented.
- `field_check.py` — Interactive field mapping review utility, lets you review and update Jira custom field mappings before import.
- `jira_check_transitions.py` — Utility to inspect available status transitions for specific issues (useful for troubleshooting bulk transitions).
- `requirements.txt` — Python dependencies (`requests`, `python-dotenv`).
- `output.csv` — Output file, always in project root, includes Created Issue ID.
- `bulk_transition_issues.csv` — Export file specifically for bulk transitions (generated by `jira_export_my_issues.py`).
- `transition_report.csv` — Detailed report of bulk transition results (generated by `jira_bulk_transition.py`).
- `tracker.csv` — Persistent log of all imported issues.
- `jira_fields.json` — Auto-fetched Jira field metadata for field mapping and debugging.
- `error.log` — All logging output (console + file).
- `main_menu.log` — Menu system activity and operation logs.
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

## Version

- **V1.32 (Stable)** — **Unified Menu Interface:** Added comprehensive menu system (`main.py`) with organized function groups, keyboard shortcuts, automated workflows, and continuous operation. Features emoji-enhanced interface, activity logging, and streamlined user experience. Option 7 provides automated export → bulk transition workflow. All previous v1.31 features retained.

- **V1.31 (Stable)** — **Bulk Transition Feature:** Added `jira_bulk_transition.py` for intelligent bulk status transitions with smart issue-type detection. Supports automatic status selection (Epic/Story→Closed, Task/Sub-task→Done) and manual override. Enhanced `jira_export_my_issues.py` with pagination support for large datasets (300+ issues). Includes comprehensive reporting, error handling, and 99.7% success rate validation. All previous features from v1.30 retained.

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

- **V1.31 (Stable)** — **Bulk Transition Feature:** Added `jira_bulk_transition.py` for intelligent bulk status transitions with smart issue-type detection. Supports automatic status selection (Epic/Story→Closed, Task/Sub-task→Done) and manual override. Enhanced `jira_export_my_issues.py` with pagination support for large datasets (300+ issues). Includes comprehensive reporting, error handling, and 99.7% success rate validation. All previous features from v1.30 retained.

- **V1.30 (Stable)** — Resolution Status Management expanded: Now supports 6 options (Done, In Progress, Backlog, Done All, In Progress All, Backlog All) for status/transition selection. The "All" options apply the selected status to all issues and sub-tasks without further prompts. All other features from v1.29 retained. This is a stable release.

---
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with unified menu interface, bulk transition capabilities, full traceability, error handling, and a fully maintainable, production-ready codebase.*
