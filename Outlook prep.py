# Outlook prep.py
# Script for preparing Outlook/Teams calendar export CSVs for Jira import.
# - Cleans and reformats calendar CSVs to match Jira work item format
# - Handles date/time normalization, summary extraction, and mapping to Jira fields
# - Usage: Run via main menu for calendar CSVs before importing to Jira

import csv
import re
from datetime import datetime, timedelta
import pytz

# Define the mapping of Outlook/Teams fields to Jira fields
FIELD_MAPPING = {
    "Subject": "summary",
    "Start Date": "customfield_10000",
    "Start Time": "customfield_10001",
    "End Date": "customfield_10002",
    "End Time": "customfield_10003",
    "Description": "description",
    "Location": "customfield_10004",
    "Attendees": "customfield_10005",
}

# Define the date and time format used in the calendar CSVs
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M %p"

def clean_subject(subject):
    """Clean and extract the summary from the subject field."""
    # Remove any leading/trailing whitespace
    subject = subject.strip()
    # Limit the summary to 255 characters
    return subject[:255]

def convert_datetime(date_str, time_str, tzinfo):
    """Convert the date and time strings to a timezone-aware datetime object."""
    # Parse the date and time strings
    naive_dt = datetime.strptime(f"{date_str} {time_str}", f"{DATE_FORMAT} {TIME_FORMAT}")
    # Localize the datetime to the specified timezone
    return tzinfo.localize(naive_dt)

def normalize_row(row, tzinfo):
    """Normalize the row data to match the Jira work item format."""
    # Extract and clean the subject
    row["summary"] = clean_subject(row["Subject"])
    # Convert the start and end date/time to UTC
    start_dt = convert_datetime(row["Start Date"], row["Start Time"], tzinfo)
    end_dt = convert_datetime(row["End Date"], row["End Time"], tzinfo)
    # Calculate the duration in hours
    duration = (end_dt - start_dt).total_seconds() / 3600.0
    # Map the row data to the Jira fields
    normalized_row = {
        "fields": {
            "summary": row["summary"],
            "customfield_10000": start_dt.strftime(DATE_FORMAT),
            "customfield_10001": start_dt.strftime(TIME_FORMAT),
            "customfield_10002": end_dt.strftime(DATE_FORMAT),
            "customfield_10003": end_dt.strftime(TIME_FORMAT),
            "description": row["Description"],
            "customfield_10004": row["Location"],
            "customfield_10005": row["Attendees"],
            "customfield_10006": duration,
        }
    }
    return normalized_row

def main(input_file, output_file, timezone):
    """Main function to clean and reformat the calendar CSV for Jira import."""
    # Set the timezone info
    tzinfo = pytz.timezone(timezone)
    # Read the input CSV file
    with open(input_file, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        # Normalize each row and collect the results
        normalized_rows = [normalize_row(row, tzinfo) for row in reader]
    # Write the output CSV file
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = normalized_rows[0]["fields"].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized_rows:
            writer.writerow(row["fields"])

# The script expects the input and output file paths and the timezone as command-line arguments
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <input_file> <output_file> <timezone>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    timezone = sys.argv[3]
    main(input_file, output_file, timezone)