# JiraCSVtoAPI Automation Toolkit

## Setup and Installation

### Prerequisites

Before using this toolkit, you need to set up your development environment. Follow these steps to get everything ready:

### 1. Install Python

**For macOS:**
- **Option A - Using Homebrew (Recommended):**
  ```bash
  # Install Homebrew if you don't have it
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  
  # Install Python
  brew install python
  ```

- **Option B - Download from Python.org:**
  1. Visit [python.org/downloads](https://www.python.org/downloads/)
  2. Download Python 3.9 or later
  3. Run the installer and follow the prompts
  4. **Important:** Check "Add Python to PATH" during installation

**For Windows:**
1. Visit [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.9 or later
3. Run the installer
4. **Important:** Check "Add Python to PATH" during installation
5. Choose "Install for all users" if prompted

**For Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Verify Python Installation

Open a terminal/command prompt and verify Python is installed correctly:

```bash
python3 --version
# Should show Python 3.9.x or later

pip3 --version
# Should show pip version information
```

**Note for Windows:** You may need to use `python` and `pip` instead of `python3` and `pip3`.

### 3. Clone or Download the Repository

**Option A - Using Git (Recommended):**
```bash
git clone https://github.com/JLopes-Enablon/JiraCSVtoAPI.git
cd JiraCSVtoAPI
```

**Option B - Download ZIP:**
1. Go to the [GitHub repository](https://github.com/JLopes-Enablon/JiraCSVtoAPI)
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file and navigate to the folder

### 4. Set Up Virtual Environment

**Create and activate a virtual environment:**

**For macOS/Linux:**
```bash
# Navigate to the project directory
cd JiraCSVtoAPI

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# You should see (.venv) in your terminal prompt
```

**For Windows:**
```cmd
# Navigate to the project directory
cd JiraCSVtoAPI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# You should see (.venv) in your command prompt
```

### 5. Install Required Packages

With your virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For Jira API communication
- `python-dotenv` - For environment variable management
- `pytest` - For running tests
- `pytz` - For timezone handling

### 6. Verify Installation

Test that everything is working correctly:

```bash
python main.py
```

You should see the Jira Management Toolkit menu appear. Press `Ctrl+C` or `0` to exit.

### 7. Deactivating the Virtual Environment

When you're done working with the toolkit, you can deactivate the virtual environment:

```bash
deactivate
```

### 8. Future Usage

Every time you want to use the toolkit:

1. **Navigate to the project directory:**
   ```bash
   cd JiraCSVtoAPI
   ```

2. **Activate the virtual environment:**
   - **macOS/Linux:** `source .venv/bin/activate`
   - **Windows:** `.venv\Scripts\activate`

3. **Run the toolkit:**
   ```bash
   python main.py
   ```

### Troubleshooting

**Common Issues:**

- **"python: command not found"**: Make sure Python is installed and added to your PATH
- **"No module named 'requests'"**: Make sure you activated the virtual environment and ran `pip install -r requirements.txt`
- **Permission errors**: On macOS/Linux, you may need to use `python3` and `pip3` instead of `python` and `pip`

**Getting Help:**
If you encounter issues during setup, please check that:
1. Python 3.9+ is installed and in your PATH
2. You've activated the virtual environment (you should see `(.venv)` in your prompt)
3. All requirements are installed (`pip list` should show the required packages)

## Getting Required Jira Variables

Before using this toolkit, you will need the following Jira variables:

- **JIRA_URL**: Your Jira Cloud or Server URL (e.g., `https://your-domain.atlassian.net`)
  - **How to get it:** Log in to your Jira account in your browser. Copy the base URL from your browser's address bar (it will look like `https://your-domain.atlassian.net`).

- **JIRA_EMAIL**: The email address associated with your Jira account
  - **How to get it:** Click your profile icon in the top right corner of Jira, then select "Profile". Your email address will be shown on your profile page.

- **JIRA_TOKEN**: A Jira API token
  - **How to get it:**
    1. Go to [Jira API tokens page](https://id.atlassian.com/manage-profile/security/api-tokens).
    2. Click "Create API token".
    3. Enter a label (e.g., "JiraCSVtoAPI") and click "Create".
    4. Copy the generated token and save it securely (you will need to paste it into the script prompt).

- **JIRA_PROJECT_ID**: The key of your Jira project (e.g., `PROJKEY`)
  - **How to get it:**
    1. In Jira, open your project.
    2. The project key is shown in the project sidebar and in the URL (e.g., `https://your-domain.atlassian.net/jira/software/projects/PROJKEY/boards/1` — here, `PROJKEY` is the project key).

- **JIRA_ASSIGNEE** (optional): Username or account ID to assign issues
  - **How to get it:**
    1. In Jira, click on your profile icon and select "Profile" to see your username/account ID.
    2. For other users, go to "People" in the top menu, search for the user, and click their name to view their details.

You will be prompted for these when running the scripts for the first time. They are stored in a `.env` file for future runs.

## Required CSV Format for Input

If you are not importing from and Outlook CSV your input CSV must have the following columns (header row required):

```
Project,Summary,IssueType,Parent,Start Date,Story Points,Original Estimate,Time spent,Priority
```
If you are using an Outlook generated CSV export. this needs to include these fields at a minimum, this will automatically convert the date into the fields above.
```
Subject,Start Date, Start Time, End Time


**Notes:**
- `IssueType` can be `Epic`, `Story`, `Task`, or `Sub-task` (case-insensitive)
- `Parent` is the parent issue key (for sub-tasks or linked stories)
- `Start Date` should be in `YYYY-MM-DD` format
- `Story Points` and `Original Estimate` are optional but recommended (Pending change from Jira admins to be enabled for API)
- `Created Issue ID` will be filled in by the script after import

## Overview
This toolkit automates the process of importing issues and work items into Jira from CSV files. It supports both pre-formatted work item CSVs and calendar exports (Outlook/Teams), providing scripts for cleaning, mapping, and bulk importing data.

## Features
- Import pre-formatted Jira work item CSVs
- Prepare Outlook/Teams calendar exports for Jira import
- Bulk create issues and sub-tasks in Jira via REST API
- Update Story Points and Original Estimate fields for Stories
- Map CSV columns to Jira fields, including custom fields
- Check and map Jira field metadata
- Menu-driven workflow for easy selection and execution

## Scripts
- `main.py`: Main menu and workflow selection
- `jiraapi.py`: Bulk import and field update logic
- `Outlook prep.py`: Calendar CSV cleaning and formatting
- `field_check.py`: Field mapping and metadata check

## Usage
1. Run `main.py` to start the toolkit and select your workflow:
   - Option 1: Import Calendar Export (Outlook/Teams) to Jira (Default)
   - Option 2: Import pre-formatted Jira work item CSVs
2. Follow prompts to clean, map, and import your data.
3. Use `field_check.py` to verify field mapping if needed.

## Requirements
- Python 3.9+
- Required packages listed in `requirements.txt`

## Example CSVs
- `output.csv`, `June.CSV`, `Outlook.csv`, `mystuff.csv`: Example files for different import workflows

## Notes
- Ensure correct field mapping for custom fields (e.g., Story Points)
- For calendar exports, run `Outlook prep.py` before importing to Jira

## Detailed Functions and Features

Below is a detailed overview of the main functions and features provided by this toolkit:

### Main Scripts

- **main.py**
  - Provides a menu-driven interface for users to select workflows.
  - Handles user input and launches the appropriate scripts for importing work items or preparing calendar exports.
  - Ensures a guided, user-friendly experience for bulk operations.

- **jiraapi.py**
  - Core logic for importing issues and sub-tasks into Jira from CSV files.
  - Handles authentication, environment variable management, and API communication.
  - Supports bulk creation of issues, sub-tasks, and updates to fields like Story Points and Original Estimate.
  - Includes error handling, logging, and field mapping logic.
  - Prompts for required variables and stores them securely in a `.env` file.

- **Outlook prep.py**
  - Cleans and formats Outlook/Teams calendar CSV exports for Jira import.
  - Normalizes event data, removes unnecessary columns, and outputs a compatible CSV for further processing.
  - Ensures calendar data is ready for bulk import as work items.

- **field_check.py**
  - Checks and maps CSV columns to Jira fields, including custom fields.
  - Helps users verify that their CSV headers match the expected Jira field names and IDs.
  - Can be used independently to troubleshoot field mapping issues.

- **jira_field_names_export.py**
  - Exports all available Jira field metadata to a CSV file.
  - Useful for advanced users who need to map or reference custom fields in their imports.

- **jira_bulk_transition.py**
  - Allows bulk transitioning of issues (e.g., moving multiple issues to a new status) via the Jira API.
  - Can be used after import to update workflow states in bulk.

- **jira_check_transitions.py**
  - Checks available transitions for a given Jira issue key.
  - Helps users understand which workflow states are available for a specific issue.

- **jira_export_my_issues.py**
  - Exports all issues assigned to or reported by the current user to a local CSV file.
  - Useful for backup, reporting, or further processing.

### Key Features

- **Bulk Import**: Import multiple issues and sub-tasks from a single CSV file, reducing manual entry and errors.
- **Calendar Integration**: Prepare and import Outlook/Teams calendar events as Jira work items, streamlining time tracking and reporting.
- **Field Mapping**: Map CSV columns to Jira fields, including support for custom fields and field validation.
- **Menu-Driven Workflow**: User-friendly menu system for selecting and executing workflows without needing to remember script names or arguments.
- **Environment Management**: Securely prompts for and stores Jira credentials and configuration in a `.env` file, keeping sensitive data out of source code.
- **Error Handling & Logging**: Comprehensive error messages and logging to help diagnose issues during import or API operations.
- **Transition Management**: Bulk transition issues to new workflow states, and check available transitions for any issue.
- **Export Capabilities**: Export your own issues from Jira for backup, migration, or analysis.

### Helper and Test Scripts

- **test_fixes.py**: Contains tests for field update logic, ensuring Story Points and Original Estimate updates work as expected.
- **fix_field_updates.py**: Utility for testing and fixing field update behaviors in Jira.

### File Structure Notes

- **output.csv, Outlook.csv, June.CSV, mystuff.csv**: Example and output files for different workflows.
- **.env**: Stores Jira credentials and configuration (excluded from version control).
- **requirements.txt**: Lists all required Python packages for the toolkit.
- **.gitignore**: Ensures sensitive and output files are not committed to version control.

For more details on each script, see the inline comments and docstrings within the codebase.
For help feel free to teach out.