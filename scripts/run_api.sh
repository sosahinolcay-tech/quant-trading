#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r api/requirements.txt

cd "$ROOT_DIR/api"
PYTHONPATH="$ROOT_DIR" uvicorn main:app --reload --host 127.0.0.1 --port 8010
