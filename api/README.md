# Quant Trading API

Run the API locally:

1) Create a virtual environment and install API dependencies from the repo root:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r api/requirements.txt`

2) Start the server (from `api/`):
   - `PYTHONPATH=".." uvicorn main:app --reload --host 127.0.0.1 --port 8010`

Key endpoints:
- `GET /health`
- `POST /data/quality`
- `POST /data/prices`
- `POST /data/fundamentals`
- `GET /data/news`
- `GET /providers/status`
- `POST /run/market-maker`
- `POST /run/pairs`
- `POST /walk-forward`
