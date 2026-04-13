import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import MAX_FILE_SIZE_BYTES
from app.schemas import ProcessResponse, SessionListItem
from app.agents.graph import run_graph
from app.parsers import parse
from app.storage.database import init_db, get_db
from app.storage.models import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database")
    await init_db()
    yield
    logger.info("Shutting down")


app = FastAPI(title="StudyMate API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)  # exposes /metrics


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # ── Validate ──────────────────────────────────────────────────────────
    allowed = {"pdf", "docx", "doc", "txt"}
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")

    logger.info(f"Received file: {file.filename} ({len(content)} bytes)")

    # ── Parse ─────────────────────────────────────────────────────────────
    try:
        text = await parse(content, file.filename or "file.txt")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        raise HTTPException(status_code=422, detail="Could not extract text from file")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text found in file")

    # ── Run agents ────────────────────────────────────────────────────────
    result = await run_graph(text)

    # ── Persist ───────────────────────────────────────────────────────────
    session_id = str(uuid.uuid4())
    db_session = Session(
        id=session_id,
        filename=file.filename or "unknown",
        summary=result["summary"],
        flashcards=[fc.model_dump() for fc in result["flashcards"]],
        quiz=[q.model_dump() for q in result["quiz"]],
    )
    db.add(db_session)
    await db.commit()

    logger.info(f"Session saved: {session_id}")

    return ProcessResponse(
        session_id=session_id,
        filename=file.filename or "unknown",
        summary=result["summary"],
        flashcards=result["flashcards"],
        quiz=result["quiz"],
    )


@app.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Session).order_by(Session.created_at.desc()).limit(50))
    sessions = rows.scalars().all()
    return [
        SessionListItem(
            session_id=s.id,
            filename=s.filename,
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}", response_model=ProcessResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(Session, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return ProcessResponse(
        session_id=row.id,
        filename=row.filename,
        summary=row.summary,
        flashcards=row.flashcards,
        quiz=row.quiz,
    )
