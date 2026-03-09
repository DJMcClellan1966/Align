"""YOUI backend API: intent, helpers, query, feedback, suggest."""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .intent import create_helper_from_intent, list_user_helpers, get_template_for_intent, load_intent_templates
from .retrieve import retrieve
from .memory import append_feedback, get_recent_feedback, get_useful_context
from .truth_base import load_truth_base

app = FastAPI(title="YOUI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORPUS_DIR = Path(os.environ.get("YOUI_CORPUS_DIR", str(Path(__file__).resolve().parent.parent / "data" / "user_helpers")))
TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "config" / "intent_templates.json"


class IntentRequest(BaseModel):
    intent: str


class IntentResponse(BaseModel):
    helper_id: str
    vertical_slug: str
    statement_count: int


class QueryRequest(BaseModel):
    helper_id: str
    message: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    user_context_used: bool


class FeedbackRequest(BaseModel):
    helper_id: str
    query: str
    response: str
    useful: bool
    note: str = ""


class SuggestResponse(BaseModel):
    suggestions: list[str]
    based_on: str


@app.post("/intent", response_model=IntentResponse)
def post_intent(body: IntentRequest):
    """Create or resolve a helper from user intent text."""
    intent = (body.intent or "").strip()
    if not intent:
        raise HTTPException(status_code=400, detail="intent is required")
    try:
        helper_id, truth_base_path, count = create_helper_from_intent(
            intent,
            out_dir=CORPUS_DIR,
            templates_path=TEMPLATES_PATH,
        )
        templates = load_intent_templates(TEMPLATES_PATH)
        vertical_slug = get_template_for_intent(intent, templates) or "general"
        return IntentResponse(
            helper_id=helper_id,
            vertical_slug=vertical_slug,
            statement_count=count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/helpers")
def get_helpers():
    """List all user helpers."""
    helpers = list_user_helpers(CORPUS_DIR)
    return {"helpers": helpers}


@app.get("/helpers/{helper_id}")
def get_helper(helper_id: str):
    """Get one helper by id (meta + statement count)."""
    helpers = list_user_helpers(CORPUS_DIR)
    for h in helpers:
        if h["helper_id"] == helper_id:
            path = Path(h["truth_base_path"])
            statements = load_truth_base(path)
            return {
                **h,
                "statement_count": len(statements),
            }
    raise HTTPException(status_code=404, detail="Helper not found")


@app.post("/query", response_model=QueryResponse)
def post_query(body: QueryRequest):
    """Run retrieval over helper's truth base and form an answer from citations."""
    helpers = list_user_helpers(CORPUS_DIR)
    truth_base_path = None
    for h in helpers:
        if h["helper_id"] == body.helper_id:
            truth_base_path = h["truth_base_path"]
            break
    if not truth_base_path:
        raise HTTPException(status_code=404, detail="Helper not found")

    citations, user_context = retrieve(
        body.message,
        truth_base_path,
        helper_id=body.helper_id,
        top_k=5,
        include_user_context=True,
    )

    # Build a simple answer from cited statements (no LLM in v0)
    parts = []
    if user_context:
        parts.append("Based on your past useful feedback:\n" + "\n".join(user_context[:3]))
    parts.append("From your knowledge base:")
    for i, c in enumerate(citations, 1):
        parts.append(f"{i}. {c.get('text', '')}")
    answer = "\n\n".join(parts) if parts else "No matching knowledge for that question. Try rephrasing or add more to your helper."

    return QueryResponse(
        answer=answer,
        citations=citations,
        user_context_used=len(user_context) > 0,
    )


@app.post("/feedback")
def post_feedback(body: FeedbackRequest):
    """Record feedback for learning from use."""
    append_feedback(
        body.helper_id,
        body.query,
        body.response,
        body.useful,
        body.note,
    )
    return {"ok": True}


@app.get("/suggest", response_model=SuggestResponse)
def get_suggest(helper_id: str):
    """Return suggestions based on user's goals and past useful interactions."""
    helpers = list_user_helpers(CORPUS_DIR)
    meta_path = None
    for h in helpers:
        if h["helper_id"] == helper_id:
            meta_path = Path(h["truth_base_path"]).parent / "meta.json"
            break
    if not meta_path or not meta_path.exists():
        raise HTTPException(status_code=404, detail="Helper not found")

    import json
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    intent = meta.get("intent", "")

    user_context = get_useful_context(helper_id, limit=10)
    suggestions = []
    if intent:
        suggestions.append(f"Revisit your goal: \"{intent}\"")
    if user_context:
        suggestions.append("Topics you found useful before might be worth revisiting.")
    suggestions.append("Ask a specific question to get tailored answers from your knowledge base.")

    return SuggestResponse(
        suggestions=suggestions,
        based_on="your goal and past feedback",
    )


@app.get("/health")
def health():
    return {"status": "ok"}
