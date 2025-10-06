# CSV Behavior Fix - Source vs Tracker

## Issue Fixed
The system was incorrectly updating the source CSV file (output.csv) with Created Issue IDs. This should only happen in tracker.csv.

## Correct Behavior (Now Implemented)

### ✅ Source CSV (output.csv)
- **Should remain UNCHANGED** 
- No Created Issue ID column should be added
- Original data stays intact for future imports
- This is your "input" file that can be processed multiple times

### ✅ Tracker CSV (output/tracker.csv)  
- **Gets the Created Issue IDs**
- Maintains complete historical record
- Only newly created issues are appended (no duplicates)
- This is your "output" file for tracking what was created

## Code Changes Made

### Removed from jiraapi.py:
```python
# OLD CODE (REMOVED):
# Write back the Created Issue ID to output/output.csv for tracking
output_csv_path = os.path.join(output_dir, "output.csv")
with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=all_rows[0].keys())
    writer.writeheader()
    for row in all_rows:
        writer.writerow(row)
```

### Kept in jiraapi.py:
```python
# NEW CODE (CORRECT):
# Append only newly created issues to output/tracker.csv for persistent tracking
# NOTE: The source CSV file (output.csv) is NOT modified - only tracker.csv gets the Created Issue IDs
```

## File Behavior Summary

| File | Purpose | Gets Modified? | Contains Created Issue IDs? |
|------|---------|---------------|----------------------------|
| `your_source.csv` | Input data | ❌ No | ❌ No |
| `output/output.csv` | Copy of source | ❌ No | ❌ No |
| `output/tracker.csv` | Historical tracking | ✅ Append only | ✅ Yes |

## Current Status

✅ **Fixed**: Source CSV files remain unchanged  
✅ **Working**: Only tracker.csv gets Created Issue IDs  
✅ **Verified**: Test entry CPESG-11786 properly in tracker.csv  
✅ **Cleaned**: Removed test data from output.csv  

## Usage
When you run your script:
1. Source CSV stays exactly as it was
2. Issues get created in Jira
3. Only tracker.csv gets the new Created Issue IDs appended
4. You can re-run the same source CSV file anytime