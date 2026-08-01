#!/usr/bin/env bash
# Run the legal database web UI
cd "$(dirname "$0")"
echo "Starting Iran Legal DB web UI on http://127.0.0.1:5050 ..."
python3 web/app.py
