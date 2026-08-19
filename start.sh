#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating a local folder for this app..."
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    python -m venv .venv
  fi
fi

# shellcheck disable=SC1091
. .venv/bin/activate

echo "Installing needed files..."
python -m pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

echo "Checking for an official update..."
python scripts/sfts_overlay.py --daily || true

echo "Starting the app. A browser window should open soon..."
exec streamlit run app.py
