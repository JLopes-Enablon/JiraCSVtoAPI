# Tracker.csv Append Fix - Summary

## Issue Identified
The script was not properly appending newly created issue details to `tracker.csv`. Instead, it was either:
1. Not appending anything, or
2. Appending ALL rows (including existing ones), causing duplicates

## Root Cause
In the `import_stories_and_subtasks()` function in `jiraapi.py`, the tracker append logic around line 1163 was appending **all rows** to the tracker file instead of only the **newly created** issues.

**Original problematic code:**
```python
# Append all rows to output/tracker.csv for persistent tracking
for row in all_rows:
    tracker_writer.writerow(row)
```

## Solution Implemented

### 1. Track Initially Empty Rows
Added logic to track which rows initially had no "Created Issue ID":

```python
# Track which rows were initially empty (for tracker.csv)
initially_empty_indices = set()

# During CSV reading...
if not row.get("Created Issue ID"):
    initially_empty_indices.add(idx)
    # ... process the row
```

### 2. Append Only Newly Created Issues
Modified the tracker append logic to only add rows that:
- Were initially empty (no Created Issue ID)
- Now have a Created Issue ID (after processing)

```python
# Append only newly created issues to output/tracker.csv
new_issues = []
for idx, row in enumerate(all_rows):
    if idx in initially_empty_indices and row.get("Created Issue ID"):
        new_issues.append(row)

if new_issues:
    # Append to tracker.csv...
    logger.info(f"Appended {len(new_issues)} newly created issues to {tracker_path}")
```

### 3. Fixed Missing Method
Also fixed a missing `get_available_resolutions()` method that was causing runtime errors.

## Test Results

✅ **Test Passed**: `test_tracker_append.py`
- Created 1 test issue
- Tracker.csv went from 589 to 590 entries (exactly +1)
- Correct test item was appended
- No duplicates or incorrect entries

## Current Behavior

### ✅ What Works Now:
1. **Proper Tracking**: Only newly created issues are appended to `tracker.csv`
2. **No Duplicates**: Previously created issues are not re-appended
3. **Persistent History**: `tracker.csv` maintains a complete history of all created issues
4. **Output.csv Updated**: The source `output.csv` is still updated with Created Issue IDs
5. **Logging**: Clear log messages show how many items were appended

### 📂 File Behavior:
- **`output/output.csv`**: Gets updated with Created Issue IDs for the current run
- **`output/tracker.csv`**: Gets appended with only the newly created issues (persistent history)

## Usage
When you run your script now:
1. It will process CSV rows that don't have a "Created Issue ID"
2. Create the corresponding Jira issues
3. Update the source CSV with the new Issue IDs
4. **Append only the newly created entries to tracker.csv**

The tracker.csv file now properly maintains a complete historical record of all work items created by the script, without duplicates.