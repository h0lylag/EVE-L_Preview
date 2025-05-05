#!/usr/bin/env bash
# run-eve-preview.sh  – always executes main.py as root, from the project dir
# -----------------------------------------------------

PROJECT_DIR="/home/chris/scripts/EVE-L_Preview"

# If we’re not root, re‑invoke through sudo and keep env vars
if [[ "$EUID" -ne 0 ]]; then
    exec sudo -E "$0" "$@"
fi

# Switch to the project directory
cd "$PROJECT_DIR" || { echo "[ERROR] Failed to cd to $PROJECT_DIR"; exit 1; }

# Launch Python (exec replaces this shell)
exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/main.py" "$@"
