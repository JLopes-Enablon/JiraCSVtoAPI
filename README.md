# JiraCSVtoAPI Automation Toolkit

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
   - Option 1: Import pre-formatted Jira work item CSVs
   - Option 2: Prepare Outlook/Teams calendar exports for Jira import
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

## License
MIT
