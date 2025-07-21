import sys
import os
# Ensure project root is in sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Outlook Prep Script for Jira CSV Import
# This script processes Outlook calendar CSV exports and prepares them for Jira import.
# It normalizes headers, cleans data, reformats dates, calculates durations, and prompts the user for Jira-specific fields.

import csv
import datetime
import argparse

# Helper to get week number from date string (expects YYYY-MM-DD or similar)
def get_week_of_year(date_str):
    """Get ISO week number from a date string (YYYY-MM-DD)."""
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return f"Week{date_obj.isocalendar()[1]}"

# Helper to calculate time difference and format as Jira xh xm
def get_jira_duration(start_time, end_time):
    """Calculate Jira duration string (xh ym) from start and end time (HH:MM:SS)."""
    def parse_time(t):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.datetime.strptime(t, fmt)
            except ValueError:
                continue
        raise ValueError(f"Time '{t}' is not in a recognized format (expected HH:MM or HH:MM:SS)")
    start = parse_time(start_time)
    end = parse_time(end_time)
    delta = end - start
    total_minutes = delta.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"

# Cleans up the CSV: removes quotes, strips whitespace, and normalizes date formats.
def remove_quotes_and_fix_dates(input_csv, temp_csv):
    import re
    def fix_date(date_str):
        # Match d/m/yyyy or dd/mm/yyyy and convert to yyyy-mm-dd
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        # Match d/m/yy or dd/mm/yy and convert to yyyy-mm-dd (assume 2000+)
        match_yy = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', date_str)
        if match_yy:
            day, month, year = match_yy.groups()
            year = str(int(year) + 2000)  # Assumes 21 -> 2021, 25 -> 2025
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str
    with open(input_csv, encoding='utf-8') as infile, open(temp_csv, 'w', encoding='utf-8', newline='') as outfile:
        lines = infile.readlines()
        if not lines:
            return
        # Remove quotes and strip whitespace from header, and rename 'Subject' to 'Summary' before writing
        header_fields = [h.strip() for h in lines[0].replace('"', '').strip().split(',')]
        header_fields = ["Summary" if h == "Subject" else h for h in header_fields]
        header = ','.join(header_fields)
        outfile.write(header + '\n')
        # Find the index of the Start Date column
        header_fields = [h.strip() for h in header.strip().split(',')]
        try:
            date_idx = header_fields.index('Start Date')
        except ValueError:
            date_idx = None
        # Process each row, clean up, and fix date formats
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            row = [f.strip() for f in line.replace('"', '').strip().split(',')]
            if date_idx is not None and len(row) > date_idx:
                row[date_idx] = fix_date(row[date_idx])
            # Only write if row has the same number of fields as header
            if len(row) == len(header_fields):
                outfile.write(','.join(row) + '\n')

# (Legacy) Processes a cleaned Outlook CSV and writes Jira-ready output. Not used in main flow.
def process_outlook_csv(input_csv, output_csv):
    """Process a cleaned Outlook CSV and write Jira-ready output (legacy, not interactive)."""
    with open(input_csv, newline='', encoding='utf-8') as infile, open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        # Read and strip whitespace from header, remove BOM if present
        first_line = infile.readline()
        header = [h.strip().replace('\ufeff', '') for h in first_line.strip().split(',')]
        normalized_header = [h.replace('\ufeff', '').strip() for h in header]
        reader = csv.DictReader(infile, fieldnames=normalized_header)
        # Define final output headers as required by jiraapi.py
        output_headers = [
            "Project",
            "Summary",
            "IssueType",
            "Parent",
            "Start Date",
            "Story Points",
            "Original Estimate",
            "Time spent",
            "Priority",
            "Created Issue ID"
        ]
        # Ensure there is no stray code here. The fix_date function should only exist in remove_quotes_and_fix_dates.
        writer = csv.DictWriter(outfile, fieldnames=output_headers)
        writer.writeheader()
        row_count = 0
        for i, row in enumerate(reader):
            # Skip header row
            if i == 0 and all(k == v for k, v in row.items()):
                continue
            # Strip whitespace and BOM from all values and keys
            row = {k.replace('\ufeff', '').strip(): (v.strip() if v else '') for k, v in row.items()}
            if not any(row.values()):
                continue
            # Remove rows with 'Cancelled' or 'Out of Office' in the summary (case-insensitive, also handle 'Canceled')
            summary_text = row.get('Summary', '').lower()
            if 'cancelled' in summary_text or 'canceled' in summary_text or 'out of office' in summary_text:
                continue
            try:
                week = get_week_of_year(row["Start Date"])
                original_estimate = get_jira_duration(row["Start Time"], row["End Time"])
                # Convert Jira duration (e.g., '1h 30m') to float hours for Story Points
                def duration_to_hours(duration):
                    hours = 0.0
                    if 'h' in duration:
                        h_split = duration.split('h')
                        hours += float(h_split[0].strip())
                        duration = h_split[1]
                    if 'm' in duration:
                        m_split = duration.split('m')
                        try:
                            minutes = float(m_split[0].strip())
                        except ValueError:
                            minutes = 0.0
                        hours += minutes / 60.0
                    return round(hours, 2)

                story_points = str(duration_to_hours(original_estimate)) if original_estimate else ""
                # Compose the output row
                output_row = {
                    "Project": "",  # User to fill or set default if needed
                    "Summary": f"{week} {row['Summary']}",
                    "IssueType": "Story",  # Default, user to adjust if needed
                    "Parent": "",  # User to fill if needed
                    "Start Date": row["Start Date"],
                    "Story Points": story_points,
                    "Original Estimate": original_estimate,
                    "Time spent": original_estimate,
                    "Priority": ""  # User to fill if needed
                }
                writer.writerow(output_row)
                row_count += 1
            except Exception as e:
                print(f"Error processing row: {row}\n{e}")
        print(f"Processed {row_count} rows. Fieldnames: {output_headers}")

if __name__ == "__main__":
    # === INTERACTIVE MAIN SCRIPT ===
    # Prompts the user for Jira Project ID, Issue Type, and Parent field options, then processes the CSV for Jira import.

    import os
    import shutil
    # Prompt user for Jira Project ID, Issue Type, and Parent field options
    print("\n=== Outlook Prep Automation ===\n")
    # Load Project ID from .env if available
    import sys
    project_id = ""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('JIRA_PROJECT_ID'):
                        # Support both export and non-export formats
                        val = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if val:
                            project_id = val
                            print(f"JIRA_PROJECT_ID loaded from .env: {project_id}")
                            break
        except Exception as e:
            print(f"Warning: Could not read .env for Project ID: {e}")
    # Prompt for Project ID only if not found in .env
    while not project_id:
        project_id = input("Enter the Jira Project ID (e.g., PROJ): ").strip()
        if not project_id:
            print("Project ID cannot be empty.")

    # Prompt for issue type selection
    print("What Jira issue type are you uploading?")
    print("1. Epic\n2. Story\n3. Task\n4. Sub-Task")
    while True:
        issue_type_choice = input("Enter 1, 2, 3, or 4: ").strip()
        if issue_type_choice in {"1", "2", "3", "4"}:
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
    issue_type_map = {"1": "Epic", "2": "Story", "3": "Task", "4": "Sub-task"}
    selected_issue_type = issue_type_map[issue_type_choice]

    # Optionally prompt for Parent ID for Story or Sub-task
    parent_id = ""
    auto_parent = False
    if selected_issue_type in {"Story", "Sub-task"}:
        print("\nDo you want to populate the Parent field for all entries?")
        print("1. Yes, use a single Parent ID for all entries")
        print("2. No, leave Parent blank for manual adjustment during review")
        while True:
            parent_choice = input("Enter 1 or 2: ").strip()
            if parent_choice == "1":
                parent_id = input("Enter the Parent ID to use for all entries: ").strip()
                auto_parent = True
                break
            elif parent_choice == "2":
                break
            print("Invalid choice. Please enter 1 or 2.")

    # Parse command-line arguments for input CSV and temp file
    parser = argparse.ArgumentParser(
        description="Prepare Outlook calendar CSV for Jira import.\n\nUSAGE: python 'Outlook prep.py' <input_csv> [--temp_csv TEMP_CSV]\n\nThe output will always be written as 'output.csv' in the project root, ready for jiraapi.py. Do NOT provide an output filename."
    )
    parser.add_argument("input_csv", help="Path to Outlook CSV export file")
    parser.add_argument("--temp_csv", default="temp_noquotes.csv", help="Temporary CSV file with quotes removed and dates fixed")
    args = parser.parse_args()
    # Always use output/output.csv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, "output.csv")

    # Main processing function: writes Jira-ready CSV using user selections
    def process_outlook_csv_with_type(input_csv, output_csv, project_id, selected_issue_type, auto_parent, parent_id):
        """Process cleaned Outlook CSV and write Jira-ready output using user-specified project, type, and parent."""
        with open(input_csv, newline='', encoding='utf-8') as infile, open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            first_line = infile.readline()
            header = [h.strip().replace('\ufeff', '') for h in first_line.strip().split(',')]
            normalized_header = [h.replace('\ufeff', '').strip() for h in header]
            reader = csv.DictReader(infile, fieldnames=normalized_header)
            output_headers = [
                "Project", "Summary", "IssueType", "Parent", "Start Date", "Story Points", "Original Estimate", "Time spent", "Priority", "Created Issue ID"
            ]
            writer = csv.DictWriter(outfile, fieldnames=output_headers)
            writer.writeheader()
            row_count = 0
            for i, row in enumerate(reader):
                # Skip header row
                if i == 0 and all(k == v for k, v in row.items()):
                    continue
                # Clean up row values and normalize keys to title case for robust access
                row = {k.replace('\ufeff', '').strip().title(): (v.strip() if v else '') for k, v in row.items()}
                # Robustly map 'Subject' to 'Summary' if needed
                if 'Summary' not in row and 'Subject' in row:
                    row['Summary'] = row['Subject']
                    del row['Subject']
                if not any(row.values()):
                    continue
                # Exclude cancelled/out-of-office events
                summary_text = row.get('Summary', '').lower()
                if 'cancelled' in summary_text or 'canceled' in summary_text or 'out of office' in summary_text:
                    continue
                try:
                    week = get_week_of_year(row["Start Date"])
                    # Accept both 'Start Time' and 'Start time' (and similar variants)
                    start_time = row.get("Start Time") or row.get("Start time")
                    end_time = row.get("End Time") or row.get("End time")
                    if not start_time or not end_time:
                        raise KeyError("Missing 'Start Time' or 'End Time' column in row.")
                    original_estimate = get_jira_duration(start_time, end_time)
                    # Convert Jira duration (e.g., '1h 30m') to float hours for Story Points
                    def duration_to_hours(duration):
                        hours = 0.0
                        if 'h' in duration:
                            h_split = duration.split('h')
                            hours += float(h_split[0].strip())
                            duration = h_split[1]
                        if 'm' in duration:
                            m_split = duration.split('m')
                            try:
                                minutes = float(m_split[0].strip())
                            except ValueError:
                                minutes = 0.0
                            hours += minutes / 60.0
                        return round(hours, 2)
                    story_points = str(duration_to_hours(original_estimate)) if original_estimate else ""
                    # Compose the output row for Jira import
                    output_row = {
                        "Project": project_id,
                        "Summary": f"{week} {row['Summary']}",
                        "IssueType": selected_issue_type,
                        "Parent": parent_id if auto_parent and selected_issue_type in {"Story", "Sub-task"} else "",
                        "Start Date": row["Start Date"],
                        "Story Points": story_points,
                        "Original Estimate": original_estimate,
                        "Time spent": original_estimate,
                        "Priority": "",
                        "Created Issue ID": ""
                    }
                    writer.writerow(output_row)
                    row_count += 1
                except Exception as e:
                    print(f"Error processing row: {row}\n{e}")
            print(f"Processed {row_count} rows. Fieldnames: {output_headers}")

    # Step 1: Clean up the input CSV (remove quotes, fix dates)
    remove_quotes_and_fix_dates(args.input_csv, args.temp_csv)
    # Step 2: Process the cleaned CSV and write Jira-ready output
    process_outlook_csv_with_type(args.temp_csv, output_csv, project_id, selected_issue_type, auto_parent, parent_id)
    # Step 3: Remove the temp file after processing
    try:
        os.remove(args.temp_csv)
        print(f"Removed temp file: {args.temp_csv}")
    except Exception as e:
        print(f"Warning: Could not remove temp file: {e}")
    # Step 4: Confirm output location
    generated_output = os.path.abspath(output_csv)
    if not os.path.exists(generated_output):
        print(f"Warning: Output file not found: {generated_output}")
    else:
        print(f"Output CSV is ready at: {generated_output}\n\nUSAGE: python 'jiraapi.py' output.csv\n")