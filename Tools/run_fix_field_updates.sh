#!/bin/bash
# Wrapper to auto-activate venv and run fix_field_updates.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/../.venv/bin/activate"
if [ -f "$VENV" ]; then
  source "$VENV"
fi
python "$SCRIPT_DIR/fix_field_updates.py" "$@"
