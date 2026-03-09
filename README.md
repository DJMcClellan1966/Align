# Align (YOUI – You Intelligence)

A local personal AI based on the user's needs, using verticals (hiking, finance, faith, journaling, yoga, etc.) to create a tailored helper. No large language model required for core Q&A; knowledge is stored in a truth base per helper.

## Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python run.py
```

API runs at http://localhost:8000. Optional: set `YOUI_CORPUS_DIR` to a custom path for user helpers.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL=http://localhost:8000` if the API is on a different host.

## Usage

1. On the home page, enter what you want help with (e.g. "hiking", "yoga", "finance", "faith").
2. A helper is created with a small knowledge base for that vertical; you are taken to the domain view.
3. Ask questions; answers are retrieved from the helper's truth base. Optionally mark responses as useful so the app learns.
4. Use "Suggestions" and "What should I do?" style behavior from the suggest endpoint.

## API

- `POST /intent` – Create a helper from intent text; returns `helper_id`, `vertical_slug`, `statement_count`.
- `GET /helpers` – List all helpers.
- `GET /helpers/{helper_id}` – Get one helper.
- `POST /query` – Query a helper's knowledge base; returns answer and citations.
- `POST /feedback` – Record useful/not useful for learning.
- `GET /suggest?helper_id=...` – Get suggestions based on goal and past feedback.
