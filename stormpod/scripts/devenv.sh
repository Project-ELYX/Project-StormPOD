#!/usr/bin/env bash
# Activate StormPOD venv and set PYTHONPATH

set -e
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$THIS_DIR/.venv" ]]; then
  echo "No venv found at $THIS_DIR/.venv"
  echo "Create one with:  python3 -m venv $THIS_DIR/.venv && source $THIS_DIR/.venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source "$THIS_DIR/.venv/bin/activate"
export PYTHONPATH="$THIS_DIR:$PYTHONPATH"
echo "StormPOD venv activated. PYTHONPATH=$PYTHONPATH"
