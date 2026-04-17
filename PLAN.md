# StudyMate — Implementation Plan

## Stack
- **Backend:** FastAPI + uvicorn
- **Agents:** LangGraph (state graph, parallel nodes)
- **LLM:** Ollama via OpenAI-compatible API (`openai` SDK → `localhost:11434/v1`)
- **Parsing:** pdfplumber (PDF), python-docx (DOCX), built-in (TXT)
- **Storage:** SQLAlchemy + Alembic (SQLite for dev)
- **Frontend:** Streamlit
- **Containers:** Docker + docker-compose
- **Logging:** loguru
- **Metrics:** prometheus-fastapi-instrumentator

---

## Phase 1 — Backend Skeleton ✅
- [x] Project structure (`app/`, `app/agents/`, `app/parsers/`, `app/storage/`)
- [x] `app/config.py` — settings (LLM URL, model name, DB URL)
- [x] `app/schemas.py` — Pydantic request/response models
- [x] `app/main.py` — FastAPI app, `/health` and `/process` stub
- [x] `app/agents/state.py` — LangGraph `StudyMateState` TypedDict
- [x] `app/agents/graph.py` — LangGraph graph skeleton (nodes stubbed)
- [x] `app/agents/summary.py` — SummaryAgent stub
- [x] `app/agents/flashcard.py` — FlashcardAgent stub
- [x] `app/agents/quiz.py` — QuizAgent stub
- [x] `app/parsers/__init__.py` — `parse()` dispatch function stub
- [x] `app/storage/database.py` — SQLAlchemy engine + async session
- [x] `app/storage/models.py` — `Session` ORM model

## Phase 2 — File Parsers ✅
- [x] `app/parsers/pdf.py` — extract text from PDF via pdfplumber
- [x] `app/parsers/docx.py` — extract text from DOCX via python-docx (incl. tables)
- [x] Wire up `parse()` dispatch in `app/parsers/__init__.py`
- [x] Add file size + format validation in `/process` route
- [x] Test: design_doc.pdf → 17 pages, 28 733 chars extracted correctly

## Phase 3 — LangGraph Agents ✅
- [x] `app/agents/base.py` — shared OpenAI client (→ Ollama), `call_llm()` with retry + JSON extraction
- [x] `app/agents/summary.py` — real prompt + Ollama call → 9 key points
- [x] `app/agents/flashcard.py` — real prompt + Ollama call → 13 Q&A cards
- [x] `app/agents/quiz.py` — real prompt + Ollama call → 6 MCQ with explanations
- [x] `app/agents/graph.py` — parallel execution via `asyncio.gather`
- [x] Fixed: gemma3 returns `{}` under `response_format` on complex prompts → removed constraint, added `_extract_json()` to handle raw text / code fences
- [x] All agents degrade gracefully (return [] on LLM failure, never crash the request)

## Phase 4 — Storage ✅
- [x] Save results to DB after each `/process` call (in `app/main.py`)
- [x] `GET /sessions/{id}` — retrieve past result
- [x] `GET /sessions` — list history
- [x] Table auto-created on startup via `init_db()` (Alembic skipped — overkill for SQLite dev)

## Phase 5 — Streamlit Frontend ✅
- [x] `frontend/app.py` — file upload widget (PDF / DOCX / TXT)
- [x] Summary tab — bullet list of key thesis points
- [x] Flashcards tab — expandable cards (click to reveal answer)
- [x] Quiz tab — radio buttons per question, Submit → score + per-question breakdown
- [x] Sidebar — session history from `/sessions`, click to reload any past result
- [x] Error handling — connection errors and backend errors surfaced in UI
- [x] Smoke-tested: ml_lecture.txt → 8 summary / 15 cards / 7 quiz (gemma3:12b)

## Phase 6 — Observability + Docker ✅
- [x] loguru structured logging in all agents and routes (Phases 1–3)
- [x] Prometheus metrics at `/metrics` — http_requests_total, latency histograms, GC stats
- [x] `Dockerfile` — python:3.12-slim + uv, single image for backend and frontend
- [x] `docker-compose.yml` — ollama + backend + frontend, healthchecks, volume for SQLite
- [x] `.env.example` — all env vars documented
- [x] `.dockerignore` — excludes .venv, __pycache__, .git, db file
- [ ] Traces (OpenTelemetry) — not implemented; noted as future improvement in report
- [ ] Alerting — not implemented; would require Alertmanager on top of Prometheus

---

## Directory Layout
```
multiagent-system/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── agents/
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── summary.py
│   │   ├── flashcard.py
│   │   └── quiz.py
│   ├── parsers/
│   │   ├── __init__.py   ← parse() dispatch
│   │   ├── pdf.py
│   │   └── docx.py
│   └── storage/
│       ├── database.py
│       └── models.py
├── frontend/
│   └── app.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── PLAN.md
```
