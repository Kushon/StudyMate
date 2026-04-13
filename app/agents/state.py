from typing import TypedDict
from app.schemas import Flashcard, QuizQuestion


class StudyMateState(TypedDict):
    """Shared state passed between LangGraph nodes."""
    text: str                       # parsed text from the uploaded file
    summary: list[str]              # bullet points from SummaryAgent
    flashcards: list[Flashcard]     # Q&A pairs from FlashcardAgent
    quiz: list[QuizQuestion]        # MCQ from QuizAgent
