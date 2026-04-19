#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ENTRY="$SCRIPT_DIR/运行打开我.py"
LOCAL_VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
WORKSPACE_VENV_PYTHON="/Users/wali_mini/Documents/alpha-miner/venv/bin/python"

echo "==================================="
echo "BRAIN Expression Template Decoder"
echo "==================================="
echo

# Prefer a project virtualenv to avoid Homebrew PEP 668 issues.
if [ -x "$LOCAL_VENV_PYTHON" ]; then
    PYTHON_CMD="$LOCAL_VENV_PYTHON"
elif [ -x "$WORKSPACE_VENV_PYTHON" ]; then
    PYTHON_CMD="$WORKSPACE_VENV_PYTHON"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python is not installed!"
    echo "Please install Python from https://www.python.org/"
    exit 1
fi

if [ ! -f "$APP_ENTRY" ]; then
    echo "Error: entry script not found: $APP_ENTRY"
    exit 1
fi

echo "Starting the application..."
echo "Using Python: $PYTHON_CMD"
echo

# Run the Flask application
"$PYTHON_CMD" "$APP_ENTRY"

# Check if the app exited with an error
if [ $? -ne 0 ]; then
    echo
    echo "Application exited with an error."
    read -p "Press Enter to continue..."
fi 
