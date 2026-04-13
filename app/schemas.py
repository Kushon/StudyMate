from pydantic import BaseModel


class Flashcard(BaseModel):
    question: str
    answer: str


class QuizOption(BaseModel):
    text: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str]      # 4 options
    correct_index: int      # 0-based index of the correct option
    explanation: str


class ProcessResponse(BaseModel):
    session_id: str
    filename: str
    summary: list[str]
    flashcards: list[Flashcard]
    quiz: list[QuizQuestion]


class SessionListItem(BaseModel):
    session_id: str
    filename: str
    created_at: str


class ErrorResponse(BaseModel):
    detail: str
