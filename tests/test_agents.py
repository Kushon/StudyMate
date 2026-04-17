"""
Unit tests for the three agents.
LLM calls are mocked — no Ollama required.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.state import StudyMateState
from app.agents.summary import summary_node
from app.agents.flashcard import flashcard_node
from app.agents.quiz import quiz_node
from app.schemas import Flashcard, QuizQuestion


# ── Shared fixture ─────────────────────────────────────────────────────────────

@pytest.fixture
def state() -> StudyMateState:
    return {
        "text": "Python — высокоуровневый язык программирования общего назначения.",
        "summary": [],
        "flashcards": [],
        "quiz": [],
    }


# ── SummaryAgent ───────────────────────────────────────────────────────────────

class TestSummaryAgent:

    async def test_returns_list_of_strings(self, state):
        mock = AsyncMock(return_value={
            "points": ["Python — высокоуровневый язык.", "Используется в AI и веб."]
        })
        with patch("app.agents.summary.call_llm", mock):
            result = await summary_node(state)

        assert isinstance(result["summary"], list)
        assert len(result["summary"]) == 2
        assert all(isinstance(p, str) for p in result["summary"])

    async def test_filters_empty_and_whitespace_strings(self, state):
        mock = AsyncMock(return_value={
            "points": ["Valid point", "", "   ", "Another point"]
        })
        with patch("app.agents.summary.call_llm", mock):
            result = await summary_node(state)

        assert result["summary"] == ["Valid point", "Another point"]

    async def test_missing_points_key_returns_empty(self, state):
        mock = AsyncMock(return_value={"wrong_key": ["point"]})
        with patch("app.agents.summary.call_llm", mock):
            result = await summary_node(state)

        assert result["summary"] == []

    async def test_llm_failure_returns_empty(self, state):
        mock = AsyncMock(side_effect=ValueError("LLM unavailable"))
        with patch("app.agents.summary.call_llm", mock):
            result = await summary_node(state)

        assert result["summary"] == []

    async def test_non_string_items_are_cast(self, state):
        # Model occasionally returns numbers instead of strings
        mock = AsyncMock(return_value={"points": [42, "Real point"]})
        with patch("app.agents.summary.call_llm", mock):
            result = await summary_node(state)

        # 42 becomes "42" after str() cast
        assert "Real point" in result["summary"]


# ── FlashcardAgent ─────────────────────────────────────────────────────────────

class TestFlashcardAgent:

    async def test_returns_flashcard_objects(self, state):
        mock = AsyncMock(return_value={
            "flashcards": [
                {"question": "Что такое Python?", "answer": "Высокоуровневый язык."},
                {"question": "Что такое переменная?", "answer": "Именованная ячейка памяти."},
            ]
        })
        with patch("app.agents.flashcard.call_llm", mock):
            result = await flashcard_node(state)

        assert len(result["flashcards"]) == 2
        assert all(isinstance(fc, Flashcard) for fc in result["flashcards"])

    async def test_card_has_question_and_answer(self, state):
        mock = AsyncMock(return_value={
            "flashcards": [{"question": "Q?", "answer": "A."}]
        })
        with patch("app.agents.flashcard.call_llm", mock):
            result = await flashcard_node(state)

        card = result["flashcards"][0]
        assert card.question == "Q?"
        assert card.answer == "A."

    async def test_skips_cards_with_empty_fields(self, state):
        mock = AsyncMock(return_value={
            "flashcards": [
                {"question": "", "answer": "Answer"},       # empty question
                {"question": "Question", "answer": ""},     # empty answer
                {"question": "Good Q", "answer": "Good A"}, # valid
            ]
        })
        with patch("app.agents.flashcard.call_llm", mock):
            result = await flashcard_node(state)

        assert len(result["flashcards"]) == 1
        assert result["flashcards"][0].question == "Good Q"

    async def test_skips_malformed_items(self, state):
        mock = AsyncMock(return_value={
            "flashcards": [
                "not a dict",
                None,
                {"question": "Valid Q", "answer": "Valid A"},
            ]
        })
        with patch("app.agents.flashcard.call_llm", mock):
            result = await flashcard_node(state)

        assert len(result["flashcards"]) == 1

    async def test_llm_failure_returns_empty(self, state):
        mock = AsyncMock(side_effect=ValueError("LLM unavailable"))
        with patch("app.agents.flashcard.call_llm", mock):
            result = await flashcard_node(state)

        assert result["flashcards"] == []


# ── QuizAgent ──────────────────────────────────────────────────────────────────

VALID_QUESTION = {
    "question": "Что такое Python?",
    "options": ["Язык программирования", "База данных", "Операционная система", "Браузер"],
    "correct_index": 0,
    "explanation": "Python — это язык программирования.",
}


class TestQuizAgent:

    async def test_returns_quiz_question_objects(self, state):
        mock = AsyncMock(return_value={"quiz": [VALID_QUESTION]})
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        assert len(result["quiz"]) == 1
        assert isinstance(result["quiz"][0], QuizQuestion)

    async def test_question_fields_are_correct(self, state):
        mock = AsyncMock(return_value={"quiz": [VALID_QUESTION]})
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        q = result["quiz"][0]
        assert q.question == "Что такое Python?"
        assert len(q.options) == 4
        assert q.correct_index == 0
        assert "язык программирования" in q.explanation.lower()

    async def test_skips_question_with_wrong_option_count(self, state):
        bad = {**VALID_QUESTION, "options": ["A", "B", "C"]}  # only 3 options
        mock = AsyncMock(return_value={"quiz": [bad, VALID_QUESTION]})
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        assert len(result["quiz"]) == 1  # only the valid one

    async def test_skips_question_with_out_of_range_correct_index(self, state):
        bad = {**VALID_QUESTION, "correct_index": 5}  # index 5 doesn't exist
        mock = AsyncMock(return_value={"quiz": [bad]})
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        assert result["quiz"] == []

    async def test_skips_question_with_empty_text(self, state):
        bad = {**VALID_QUESTION, "question": ""}
        mock = AsyncMock(return_value={"quiz": [bad]})
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        assert result["quiz"] == []

    async def test_llm_failure_returns_empty(self, state):
        mock = AsyncMock(side_effect=ValueError("LLM unavailable"))
        with patch("app.agents.quiz.call_llm", mock):
            result = await quiz_node(state)

        assert result["quiz"] == []

    async def test_correct_index_boundary_values(self, state):
        # 0 and 3 are valid boundaries for a 4-option question
        for idx in [0, 3]:
            q = {**VALID_QUESTION, "correct_index": idx}
            mock = AsyncMock(return_value={"quiz": [q]})
            with patch("app.agents.quiz.call_llm", mock):
                result = await quiz_node(state)
            assert result["quiz"][0].correct_index == idx
