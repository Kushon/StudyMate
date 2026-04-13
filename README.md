# StudyMate — AI Study Assistant

Upload a lecture file (PDF, DOCX, TXT) and get a **summary**, **flashcards**, and a **quiz** in one click — powered by a local LLM via Ollama.

## How it works

Three AI agents run in parallel on the uploaded text:

| Agent | Output |
|---|---|
| SummaryAgent | 7–10 key thesis points |
| FlashcardAgent | 10–15 Q&A cards |
| QuizAgent | 5–8 multiple choice questions with explanations |

Results are saved to SQLite and accessible via the session history sidebar.

## Stack

- **Backend** — FastAPI + SQLAlchemy (SQLite)
- **Agents** — LangGraph orchestration, Ollama (`gemma3:12b`)
- **Parsing** — pdfplumber (PDF), python-docx (DOCX)
- **Frontend** — Streamlit
- **Observability** — loguru logs, Prometheus metrics at `/metrics`
- **Isolation** — Docker + docker-compose

## Run locally

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) with `gemma3:12b` pulled.

```bash
# install deps
uv sync

# pull the model (once)
ollama pull gemma3:12b

# terminal 1 — backend
uv run uvicorn app.main:app --reload

# terminal 2 — frontend
uv run streamlit run frontend/app.py
```

Open **http://localhost:8501**

## Run with Docker

```bash
docker compose up --build

# first run only — pull model inside the container
docker compose exec ollama ollama pull gemma3:12b
```

| Service | URL |
|---|---|
| Frontend | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| Prometheus metrics | http://localhost:8000/metrics |

## Project structure

```
app/
├── main.py              # FastAPI routes
├── config.py            # env-based settings
├── schemas.py           # Pydantic models
├── agents/
│   ├── base.py          # shared LLM client + call_llm()
│   ├── graph.py         # orchestrator (parallel asyncio.gather)
│   ├── summary.py
│   ├── flashcard.py
│   └── quiz.py
├── parsers/             # PDF / DOCX / TXT extraction
└── storage/             # SQLAlchemy models + async session
frontend/
└── app.py               # Streamlit UI
```

## Environment variables

See `.env.example`. Key ones:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `LLM_MODEL` | `gemma3:12b` | Model name |
| `DATABASE_URL` | `sqlite+aiosqlite:///./studymate.db` | DB connection string |
| `MAX_FILE_SIZE_MB` | `10` | Upload size limit |
