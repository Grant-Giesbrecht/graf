#!/usr/bin/env bash
# Source this file from ~/.bashrc or ~/.bash_profile
# Example:
#   source /path/to/init_graf.sh /abs/path/to/project true

PROJECT_PATH="$1"
VERBOSE="$2"

if [[ -z "$PROJECT_PATH" ]]; then
    echo "Error: PROJECT_PATH not provided" >&2
    return 1
fi

# Resolve absolute path (optional but safer)
PROJECT_PATH="$(cd "$PROJECT_PATH" && pwd)"

GRAF_GRAFVIEWER_PATH="$PROJECT_PATH/src/graf/scripts/grafviewer.py"
GRAF_GRAFSCRIPT_PATH="$PROJECT_PATH/src/graf/scripts/grafscript.py"

grafviewer() {
    python "$GRAF_GRAFVIEWER_PATH" "$@"
}

grafscript() {
    python "$GRAF_GRAFSCRIPT_PATH" "$@"
}

if [[ "$VERBOSE" == "true" || "$VERBOSE" == "1" ]]; then
    echo "Added graf at path: $PROJECT_PATH"
fi
