#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

echo "Running database seed..."
PYTHONPATH=. .venv/bin/python3 scripts/seed.py

echo "Starting Brightloop M2 Backend on http://127.0.0.1:8000 (Swagger docs at /docs)"
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
