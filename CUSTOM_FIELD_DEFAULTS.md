# Custom Field Defaults Configuration

## Overview
The Jira CSV to API tool now supports setting custom field defaults via environment variables in the `.env` file. These defaults are automatically applied to all newly created issues and sub-tasks.

## Configuration

### Setting Up Custom Field Defaults

Add custom field defaults to your `.env` file using the format:
```bash
FIELD_<FIELD_NAME>=<value>
```

### Currently Supported Fields

| Field Name | Environment Variable | Jira Field ID | Type | Example Value |
|------------|---------------------|---------------|------|---------------|
| Division | `FIELD_DIVISION` | customfield_10255 | Dropdown | `Technology` |
| Business Unit | `FIELD_BUSINESS_UNIT` | customfield_10160 | Dropdown | `Corporate Technology` |
| Task Type | `FIELD_TASK_TYPE` | customfield_10609 | Dropdown | `Development` |
| IPM Managed | `FIELD_IPM_MANAGED` | customfield_10606 | Dropdown | `Yes` |
| Labels | `FIELD_LABELS` | labels | Array | `automation,csv-import,bulk-creation` |

### Example .env Configuration

```bash
# Jira API Settings
JIRA_URL='https://wkenterprise.atlassian.net'
JIRA_EMAIL='your.email@wolterskluwer.com'
JIRA_TOKEN='your-api-token'
JIRA_ASSIGNEE='your-account-id'
JIRA_PROJECT_ID='CPESG'

# Custom Field Defaults - Applied during issue creation
FIELD_DIVISION='Technology'
FIELD_BUSINESS_UNIT='Corporate Technology'
FIELD_TASK_TYPE='Development'
FIELD_IPM_MANAGED='Yes'
FIELD_LABELS='automation,csv-import,bulk-creation'
```

## How It Works

### Automatic Application
- Custom field defaults are automatically loaded from environment variables
- They are applied during **both** story and sub-task creation
- Defaults are applied **before** any CSV-specific fields
- CSV values or explicitly provided fields **override** the defaults

### Processing Logic
1. **Load Defaults**: Environment variables starting with `FIELD_` are loaded
2. **Apply to Creation**: Defaults are included in the Jira API payload
3. **Override Handling**: Any field values from CSV or explicit parameters override defaults
4. **Validation**: Invalid values are logged but don't stop the creation process

### Field Types

#### Dropdown Fields
For dropdown/select fields (Division, Business Unit, Task Type, IPM Managed):
- Use the exact option name as it appears in Jira
- Values are automatically formatted as `{"value": "option_name"}`
- Case-sensitive

#### Labels Field
For labels:
- Use comma-separated values: `label1,label2,label3`
- Spaces around commas are automatically trimmed
- Converted to array format: `["label1", "label2", "label3"]`

## Usage

### During CSV Import
When running the main CSV import:
```bash
python jiraapi.py
```
All created issues will automatically include the custom field defaults.

### Programmatic Usage
When using the API directly:
```python
from jiraapi import JiraAPI

jira = JiraAPI()

# Custom defaults are automatically applied
issue = jira.create_issue(
    project_key="CPESG",
    summary="My Story",
    issue_type="Story"
)

# You can override defaults by providing explicit values
issue = jira.create_issue(
    project_key="CPESG", 
    summary="My Story",
    issue_type="Story",
    customfield_10255={"value": "Different Division"}  # Overrides FIELD_DIVISION
)
```

## Testing

### Test Script
Run the test script to verify your configuration:
```bash
python test_custom_field_defaults.py
```

This will:
1. Load and display your custom field defaults
2. Create a test issue with defaults applied
3. Verify the fields were set correctly
4. Provide a link to view the created issue

### Manual Verification
1. Create a test issue using the script or CSV import
2. Check the issue in Jira web interface
3. Verify that all custom fields have the expected default values

## Adding New Custom Fields

To add support for additional custom fields:

1. **Find the Field ID**: Use the field export tool or check `jira_fields.json`
2. **Add to Mapping**: Update the `field_mapping` dictionary in `load_custom_field_defaults()`
3. **Add to .env**: Add your environment variable with the `FIELD_` prefix
4. **Test**: Run the test script to verify it works

### Example: Adding a new field
```python
# In jiraapi.py, update the field_mapping:
field_mapping = {
    'DIVISION': 'customfield_10255',
    'BUSINESS_UNIT': 'customfield_10160', 
    'TASK_TYPE': 'customfield_10609',
    'IPM_MANAGED': 'customfield_10606',
    'LABELS': 'labels',
    'NEW_FIELD': 'customfield_XXXXX'  # Add your new field here
}
```

```bash
# In .env file:
FIELD_NEW_FIELD='Default Value'
```

## Troubleshooting

### Common Issues

#### 1. Field Not Being Set
- **Check Spelling**: Ensure environment variable name matches exactly
- **Check Value**: Verify the value exists as an option in Jira
- **Check Permissions**: Ensure you have permission to set the field
- **Check Field ID**: Verify the customfield ID is correct

#### 2. Invalid Field Values
- **Dropdown Fields**: Must use exact option names from Jira
- **Labels**: Check for special characters or invalid label formats
- **Required Fields**: Some fields may require additional context

#### 3. API Errors
- Check the logs for detailed error messages
- Verify the field is available for the issue type
- Ensure the field is not restricted by project configuration

### Debugging
1. **Enable Debug Logging**: Set log level to DEBUG in your script
2. **Check API Payload**: The exact payload sent to Jira is logged
3. **Test Individual Fields**: Comment out fields one by one to isolate issues
4. **Use Test Script**: The test script provides detailed verification

## Benefits

### Consistency
- All issues created have consistent field values
- Reduces manual data entry and errors
- Ensures compliance with organizational standards

### Efficiency  
- No need to manually set common fields for each issue
- Bulk imports automatically include standard metadata
- Reduces post-creation field updates

### Flexibility
- Easy to update defaults by changing .env file
- Per-environment configuration (dev, staging, prod)
- Defaults can be overridden when needed

### Traceability
- All automatically created issues are properly tagged
- Easy to identify bulk-imported vs manually created issues
- Consistent labeling for reporting and filtering