# Align

A simple app where **user input** builds from a **corpus** the app they wanted. From your description (e.g. hiking, yoga, finance, faith), Align creates a helper with a small truth-base corpus and a vertical. Code is pulled from [scratchLLM](https://github.com/DJMcClellan1966/scratchLLM) and related repos; see [SOURCES.md](SOURCES.md) for what was pulled and what to pull next.

## Stack

- **Backend:** Python, FastAPI (intent → corpus, helpers).
- **Frontend:** One HTML page (submit intent, see helper result).

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python run.py
```

API runs at http://localhost:8000. Optional: set `ALIGN_CORPUS_DIR` to a custom path for user helpers.

### Frontend

Open `frontend/index.html` in a browser (or serve the folder with any static server). The page calls the API at `http://localhost:8000` by default; set `window.ALIGN_API_URL` if the API is elsewhere.

## Usage

1. Start the backend (`python run.py` from `backend/`).
2. Open `frontend/index.html`.
3. Enter what you want help with (e.g. "hiking", "yoga", "finance", "faith", "journaling").
4. Click **Create helper**. The app creates a corpus from templates and returns the helper id and vertical.

## API

- `POST /intent` – Create a helper from intent text; returns `helper_id`, `vertical_slug`, `statement_count`.
- `GET /helpers` – List all helpers.
- `GET /health` – Health check.

## CLI

From `backend/`:

```bash
python scripts/create_helper_from_intent.py "I want to go hiking"
```

## Sources and future pulls

See [SOURCES.md](SOURCES.md) for which repos were used and what to pull next (retrieve, respond, run_gui, ai4everyone, AI-Agent, AI-Bible-app).
