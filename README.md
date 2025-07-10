
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

## Security
- Credentials and sensitive variables are loaded from `.env` and only prompted for if missing.
- `.env` is updated automatically and should be kept secure.

## Version
- **V1.24** — All features above are active and working as of this version.

---
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability and error handling.*
