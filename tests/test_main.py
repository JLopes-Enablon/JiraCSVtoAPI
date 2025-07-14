import pytest
from unittest.mock import patch
import main

def test_main_menu_runs():
    # Example: Patch input/output if main.py uses them
    with patch('builtins.input', return_value='0'):
        try:
            main.main()
        except Exception as e:
            pytest.fail(f"main.main() raised an exception: {e}")

# Add more tests for main.py functions as needed
