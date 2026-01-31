# Quant Trading Frontend

This is a static frontend that talks to the FastAPI server.

Run locally:

1) Start the API:
   - `cd api`
   - `uvicorn main:app --reload --port 8000`

2) Serve the frontend:
   - `cd frontend`
   - `python3 -m http.server 5173`

Then open `http://localhost:5173` in the browser.
