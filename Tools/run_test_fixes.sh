#!/bin/bash
# Wrapper to auto-activate venv and run test_fixes.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/../.venv/bin/activate"
if [ -f "$VENV" ]; then
  source "$VENV"
fi
python "$SCRIPT_DIR/test_fixes.py" "$@"
