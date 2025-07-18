#!/usr/bin/env python3
"""
main.py - Jira Management Toolkit Menu System

A unified menu-driven interface for all Jira management operations.
Provides organized access to calendar imports, issue updates, bulk operations, and utilities.

Usage:
    python main.py

Features:
- Organized menu with logical groupings
- Keyboard shortcuts for quick access
- Automated workflows for common operations
- Continuous operation (returns to menu after each task)
- Comprehensive error handling and logging
"""

# main.py
# Main menu script for Jira CSV to API automation toolkit.
# - Provides menu options for importing pre-formatted work item CSVs and calendar exports
# - Runs appropriate scripts via subprocess based on user selection
# - Guides user through workflow for bulk import and field mapping
# - Usage: Run to start the toolkit and select desired workflow

import os
import sys
import subprocess
import logging
from datetime import datetime

sys.path.insert(0, './tools')
# Now you can import scripts from tools/ as modules

# Configure logging
logging.basicConfig(
    filename="logs/main_menu.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clear_screen():
    """Clear the terminal screen for better UX"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header with version info"""
    print("=" * 60)
    print("🚀 JIRA MANAGEMENT TOOLKIT v1.31")
    print("   Comprehensive Jira Operations Suite")
    print("=" * 60)
    print()

def print_menu():
    """Print the main menu with organized sections"""
    print("📥 IMPORT FUNCTIONS")
    print("   1. Import Pre-Formatted Work Item CSV to Jira                [I]")
    print("   2. Import Calendar Export (Outlook/Teams) to Jira             [P]")
    print()
    print("📝 ISSUE UPDATES")
    print("   3. Update existing Jira issues from CSV                      [U]")
    print("   4. Review and configure field mappings                       [C]")
    print()
    print("📊 BULK UPDATES AND EXPORTS")
    print("   5. Export my Jira issues to CSV                              [E]")
    print("   6. Bulk transition issues to completion status               [T]")
    print("   7. Complete workflow: Export → Bulk transition               [W]")
    print()
    print("🔧 SUNDRY FUNCTIONS")
    print("   8. Export Jira field metadata for reference                  [F]")
    print("   9. Check available transitions for an issue                  [R]")
    print()
    print("❌ EXIT")
    print("   0. Exit application                                          [Q]")
    print()
    print("=" * 60)

def run_script(script_name, args=None, description=""):
    """Run a script with proper error handling and logging"""
    try:
        print(f"\n🚀 {description}")
        print(f"📄 Running: {script_name}")
        print("-" * 40)
        
        # Build command
        import subprocess
        import sys
        import os
        # Use the virtual environment's python if available
        venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        if os.path.isfile(venv_python):
            cmd = [venv_python, script_name]
        else:
            cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        # Log the operation
        logging.info(f"Executing: {' '.join(cmd)}")
        
        # Run the script
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully!")
            logging.info(f"Successfully completed: {script_name}")
        else:
            print(f"\n❌ {description} encountered an error (exit code: {result.returncode})")
            logging.error(f"Error in {script_name}: exit code {result.returncode}")
            
    except FileNotFoundError:
        print(f"\n❌ Script not found: {script_name}")
        print("Please ensure the script exists in the current directory.")
        logging.error(f"Script not found: {script_name}")
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {str(e)}")
        logging.error(f"Exception in {script_name}: {str(e)}")

def export_submenu():
    """Handle the export submenu for option 5"""
    while True:
        print("\n" + "=" * 40)
        print("📤 EXPORT OPTIONS")
        print("=" * 40)
        print("1. Export focused fields (recommended for bulk transitions)")
        print("2. Export all available fields (comprehensive review)")
        print("3. Return to main menu")
        print()
        
        choice = input("Please select an option (1-3): ").strip().lower()
        
        if choice in ['1']:
            filename = input("\nEnter filename for focused export (or press Enter for 'output/bulk_transition_issues.csv'): ").strip()
            if not filename:
                filename = "output/bulk_transition_issues.csv"
            run_script("Tools/jira_export_my_issues.py", [filename], "Exporting focused fields")
            break
        elif choice in ['2']:
            filename = input("\nEnter filename for full export (or press Enter for 'my_issues_full.csv'): ").strip()
            if not filename:
                filename = "my_issues_full.csv"
            # Note: We'll need to modify jira_export_my_issues.py to support full export mode
            # For now, use the same script but with different filename
            run_script("Tools/jira_export_my_issues.py", [filename], "Exporting all fields")
            break
        elif choice in ['3']:
            break
        else:
            print("❌ Invalid option. Please select 1-3.")

def automated_workflow():
    """Handle the automated export → bulk transition workflow"""
    print("\n🔄 AUTOMATED WORKFLOW: Export → Bulk Transition")
    print("=" * 50)
    
    # Step 1: Export issues
    export_filename = "output/bulk_transition_issues.csv"
    print(f"\n📤 Step 1: Exporting issues to '{export_filename}'...")
    run_script("Tools/jira_export_my_issues.py", [export_filename], "Exporting issues for bulk transition")
    
    # Check if export was successful
    if os.path.exists(export_filename):
        print(f"\n✅ Export completed! Found '{export_filename}'")
        
        # Step 2: Ask if user wants to proceed with bulk transition
        proceed = input(f"\n🔄 Proceed with bulk transition of issues in '{export_filename}'? (y/N): ").strip().lower()
        
        if proceed == 'y':
            print(f"\n🔄 Step 2: Running bulk transition...")
            run_script("Tools/jira_bulk_transition.py", [export_filename], "Bulk transitioning issues")
            
            # Step 3: Check for transition report
            report_file = "output/transition_report.csv"
            if os.path.exists(report_file):
                print(f"\n📊 Transition report saved to '{report_file}'")
                print("💡 Review the report for detailed results and any failed transitions.")
        else:
            print("\n⏭️  Bulk transition skipped. You can run it later with option 6.")
    else:
        print(f"\n❌ Export failed - '{export_filename}' not found. Please check the export operation.")

def handle_menu_choice(choice):
    """Handle the user's menu choice"""
    choice = choice.strip().lower()
    
    if choice in ['1', 'i']:
        print("\nYou selected: Import Pre-Formatted Work Item CSV to Jira.")
        print("Use this option if your CSV is already formatted with all required Jira headers (e.g., output/output.csv, June.CSV, etc.).")
        print("If your CSV is a calendar export from Outlook or Teams, use option 2 instead.")
        run_script("jiraapi.py", [], "Importing work items to Jira")
    
    elif choice in ['2', 'p']:
        print("\nYou selected: Import Calendar Export (Outlook/Teams) to Jira.")
        print("Use this option if your CSV was exported directly from Outlook or Teams and needs formatting for Jira import.")
        print("This will run the calendar prep workflow and then import to Jira.")
        run_script("jiraapi.py", ["--prep-outlook"], "Preparing and importing calendar export via JiraAPI workflow")
        
    elif choice in ['3', 'u']:
        csv_file = input("\nEnter CSV filename to update from (or press Enter for 'output/output.csv'): ").strip()
        if not csv_file:
            csv_file = "output/output.csv"
        run_script("Tools/jira_update_fields.py", [csv_file], f"Updating existing Jira issues from {csv_file}")
        
    elif choice in ['4', 'c']:
        run_script("Tools/field_check.py", description="Reviewing and configuring field mappings")
        
    elif choice in ['5', 'e']:
        export_submenu()
        
    elif choice in ['6', 't']:
        csv_file = input("\nEnter CSV filename for bulk transition (or press Enter for 'output/bulk_transition_issues.csv'): ").strip()
        if not csv_file:
            csv_file = "output/bulk_transition_issues.csv"
        
        # Check if file exists
        if os.path.exists(csv_file):
            run_script("Tools/jira_bulk_transition.py", [csv_file], f"Bulk transitioning issues from {csv_file}")
        else:
            print(f"\n❌ File '{csv_file}' not found.")
            print("💡 Try option 5 to export your issues first, or option 7 for the complete workflow.")
            
    elif choice in ['7', 'w']:
        automated_workflow()
        
    elif choice in ['8', 'f']:
        filename = input("\nEnter filename for field metadata (or press Enter for 'jira_field_names.csv'): ").strip()
        if not filename:
            filename = "jira_field_names.csv"
        run_script("Tools/jira_field_names_export.py", [filename], "Exporting Jira field metadata")
        
    elif choice in ['9', 'r']:
        issue_key = input("\nEnter Jira issue key to check transitions (e.g., PROJ-123): ").strip()
        if issue_key:
            run_script("Tools/jira_check_transitions.py", [issue_key], f"Checking transitions for {issue_key}")
        else:
            print("❌ Issue key required.")
            
    elif choice in ['0', 'q', 'quit', 'exit']:
        return False
        
    else:
        print("❌ Invalid option. Please select from the menu or use keyboard shortcuts.")
    
    return True

def pause_for_user():
    """Pause and wait for user input before returning to menu"""
    print("\n" + "=" * 60)
    input("Press Enter to return to the main menu...")

def main():
    """Main application loop"""
    print("🚀 Starting Jira Management Toolkit...")
    logging.info("Application started")
    
    try:
        while True:
            clear_screen()
            print_header()
            print_menu()
            
            choice = input("Select an option (0-9) or use keyboard shortcuts [Q to quit]: ")
            
            if not handle_menu_choice(choice):
                break
                
            pause_for_user()
            
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user. Goodbye!")
        logging.info("Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        print("\n👋 Thank you for using Jira Management Toolkit!")
        logging.info("Application ended")

if __name__ == "__main__":
    main()
