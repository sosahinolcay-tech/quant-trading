# Quant Trading API

Run the API locally:

1) Create a virtual environment and install dependencies:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`

2) Start the server:
   - `uvicorn main:app --reload --port 8000`

Endpoints:
- `GET /health`
- `POST /data/quality`
- `POST /run/market-maker`
- `POST /run/pairs`
- `POST /walk-forward`
