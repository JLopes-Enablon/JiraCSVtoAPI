# 🚀 Jira CSV to API Automation Toolkit

A comprehensive Python toolkit for automating Jira operations via CSV imports, bulk updates, and API integration. Streamline your workflow management with powerful automation tools.

## ⚡ Quick Start

### 🎯 Main Scripts (What You Need)

This toolkit has **2 core scripts** that handle everything:

1. **`main.py`** - Interactive menu system for all operations
2. **`jiraapi.py`** - Core API engine and direct CSV import tool

### 🚀 Getting Started (3 Steps)

1. **Clone & Setup**
   ```bash
   git clone https://github.com/JLopes-Enablon/JiraCSVtoAPI.git
   cd JiraCSVtoAPI
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the Menu System**
   ```bash
   python main.py
   ```

3. **Follow the Prompts**
   - Enter your Jira credentials when prompted
   - Choose your workflow (calendar import, CSV import, etc.)
   - Let the automation handle the rest!

### 🎛️ Usage Modes

**Option A: Interactive Menu (Recommended)**
```bash
python main.py                    # Simple mode
python main.py --advanced         # Advanced mode with all options
```

**Option B: Direct CSV Import**
```bash
python jiraapi.py                 # Direct CSV to Jira import
python jiraapi.py --prep-outlook  # Outlook calendar import
```

## 📋 Prerequisites

- **Python 3.9+**
- **Jira Cloud or Server access**
- **API Token** (get from [Atlassian Account](https://id.atlassian.com/manage-profile/security/api-tokens))

## 🔑 Required Jira Information

You'll be prompted for these on first run (stored securely in `.env`):

- **JIRA_URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **JIRA_EMAIL**: Your Jira account email
- **JIRA_TOKEN**: API token from Atlassian Account Settings
- **JIRA_PROJECT_ID**: Project key (e.g., `PROJ`, `DEV`, `CPESG`)

## 📊 Supported Workflows

### 📥 Import Operations
- **Calendar Export Import**: Outlook/Teams calendar → Jira work items
- **CSV Import**: Pre-formatted work item CSV → Jira issues
- **Bulk Creation**: Stories, tasks, subtasks with custom fields

### 📝 Update Operations  
- **Bulk Field Updates**: Update existing issues from CSV
- **Story Points & Estimates**: Automated field population
- **Custom Field Defaults**: Automatic application during creation

### 📤 Export Operations
- **Issue Export**: Export your Jira issues to CSV
- **Field Metadata Export**: Export available Jira fields
- **Bulk Transition**: Move multiple issues through workflows

## 📁 CSV Format Requirements

### Standard Work Item CSV
```csv
Project,Summary,IssueType,Parent,Start Date,Story Points,Original Estimate,Priority
PROJ,Example Task,Story,,2024-10-06,5,8h,High
```

### Outlook Calendar CSV
```csv
Subject,Start Date,Start Time,End Time
Team Meeting,2024-10-06,09:00 AM,10:00 AM
```

## 🏗️ Project Structure

```
JiraCSVtoAPI/
├── main.py              # 🎛️ Interactive menu system
├── jiraapi.py            # ⚙️ Core API engine
├── README.md             # 📖 Documentation
├── requirements.txt      # 📦 Dependencies
├── sample_events.csv     # 📄 Example data
├── Tools/               # 🔧 Utility scripts
│   ├── field_check.py
│   ├── jira_export_my_issues.py
│   ├── jira_bulk_transition.py
│   └── Outlook prep.py
├── tests/               # 🧪 Test scripts
└── archive/             # 📁 Documentation & examples
```

## ✨ Key Features

### 🤖 **Automated Custom Fields**
- Configurable defaults via `.env` file
- Automatic application during issue creation
- Support for dropdowns, text fields, and labels

### 🔄 **Smart CSV Processing**
- Auto-detection of CSV formats
- Field mapping and validation
- Error handling and logging

### 📊 **Bulk Operations**
- Create hundreds of issues in minutes
- Update existing issues in bulk
- Transition multiple issues through workflows

### 🛡️ **Security & Reliability**
- Secure credential storage
- Comprehensive error handling
- Detailed logging for troubleshooting

## 🔧 Advanced Usage

### Menu System Options
```bash
# Simple mode - essential operations only
python main.py

# Advanced mode - all features
python main.py --advanced
```

### Direct API Operations
```bash
# Import pre-formatted CSV
python jiraapi.py

# Import Outlook calendar
python jiraapi.py --prep-outlook

# Custom field validation
python Tools/field_check.py
```

## 🆘 Troubleshooting

### Common Issues

**"No module named 'requests'"**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

**"Authentication failed"**
- Verify your API token is correct
- Check if your email matches your Jira account
- Ensure you have project permissions

**"Field not found errors"**
```bash
# Check field mappings
python Tools/field_check.py
```

### Getting Help

1. **Check logs**: `logs/main_menu.log` and `logs/error.log`
2. **Validate fields**: Use `Tools/field_check.py` 
3. **Test connection**: Run `python main.py` and try option 5 (Export)

## 🔄 Custom Field Defaults

The toolkit supports automatic custom field population. Configure defaults in your `.env` file:

```env
# Custom Field Defaults
FIELD_DIVISION='CP&ESG'
FIELD_BUSINESS_UNIT='CPESG-Enablon'
FIELD_TASK_TYPE='General'
FIELD_IPM_MANAGED='Yes'
FIELD_LABELS='automation'
```

These values are automatically applied when creating new issues.

## 📖 Detailed Documentation

- **Setup Guide**: See Prerequisites section above
- **CSV Formats**: Check `sample_events.csv` for examples
- **Tool Scripts**: Individual utilities in `Tools/` folder
- **Test Suite**: Validation scripts in `tests/` folder

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions or support, please open an issue in the GitHub repository.

---

**🎯 Ready to automate your Jira workflow? Start with `python main.py`!**