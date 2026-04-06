#!/bin/sh
set -eu

# This script is an optional long-running task helper.
# Fill in only the commands that are safe and useful for repeatedly
# getting the task environment into a known-good state.

# Example setup:
# python3 -m pip install -e .

# Example start command:
# PYTHONPATH=src python3 -m awh --help

# Example smoke check:
# PYTHONPATH=src python3 -m unittest discover -s tests -v

# By default this script intentionally performs no repo-specific action.
echo "Edit docs/tasks/<task-slug>/init.sh with setup, start, and smoke-check commands."
