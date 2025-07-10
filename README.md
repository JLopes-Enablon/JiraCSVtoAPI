---

# JiraCSVviaAPI-1 (V1.26)

A robust, interactive Python workflow to process Outlook calendar CSV exports for Jira import.

## Features
- **Automated CSV Cleaning & Reformatting:**
  - Cleans and normalizes Outlook CSVs for Jira import, including renaming the `Subject` column to `Summary` automatically.
  - Excludes cancelled, declined, and out-of-office events.
  - Calculates Story Points from event durations.
  - Normalizes date formats to `YYYY-MM-DD`.
- **Interactive User Prompts:**
  - Prompts for Jira Project ID, Issue Type, and Parent ID during CSV prep.
  - Optionally auto-populates the Parent field for all entries.
  - Prompts for missing .env variables and saves them for future runs.
- **Output & Idempotency:**
  - Always generates `output.csv` in the project root, ready for import.
  - Only processes rows without a `Created Issue ID` (idempotent import).
  - Appends all processed rows to `tracker.csv` for persistent tracking.
- **Jira Import Automation:**
  - Imports Epics, Stories, Tasks, and Sub-tasks from CSV.
  - Handles correct parent/epic linkage for stories and sub-tasks.
  - Supports any top-level Jira issue type.
  - Updates the Start Date field (customfield_10015, or as mapped) after issue creation for all new issues (not just Actual Start).
  - Sends Story Points as a number (float) to Jira.
  - Handles Original Estimate and Time Spent fields, using the Jira Worklog API for time tracking.
  - Logs all Jira API requests and responses for troubleshooting, including outgoing payloads and responses.
- **.env Integration:**
  - Loads sensitive variables from `.env` and prompts for missing ones, saving them for future runs.
  - Assignee logic supports Jira Cloud accountId.
- **Robust Logging & Error Handling:**
  - All logging output is written to both console and `error.log` for full traceability.
  - Logs API errors, skipped sub-tasks, and all outgoing payloads.
- **Jira Field Metadata:**
  - Fetches all Jira field metadata and saves to `jira_fields.json` before import for debugging and mapping.
- **Jira Field Mapping Review:**
  - Interactive review and update of custom field mappings (e.g., Story Points, Start Date, Actual Start) before import.
  - Prompts you to confirm or change the Jira field IDs for each mapped field, using live metadata from your Jira instance.
  - Supports mapping Start Date to any custom field.
  - **NEW:** Optionally allow Story Points and custom fields to be sent to sub-tasks (default: off, can be enabled in field mapping review step). This supports Jira instances that permit Story Points on sub-tasks.

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
- `jiraapi.py` — Main workflow: interactive, idempotent, logs API calls, .env integration, time tracking and worklog enabled, Start Date update after creation, robust error handling, and field mapping review.
- `Outlook Prep/Outlook prep.py` — CSV prep script: interactive, auto-renames headers, normalizes dates, excludes unwanted events, prompts for Jira fields, and generates output.csv.
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
- **V1.26** — Adds option to allow Story Points/custom fields on sub-tasks (configurable in field mapping review). All other features above are active and working as of this version, including Start Date post-creation update, header normalization, and robust field mapping review.

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
*This project enables secure, robust, and idempotent bulk import of Outlook calendar events into Jira, with full traceability and error handling.*
