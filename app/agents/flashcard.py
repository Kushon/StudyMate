from loguru import logger
from app.agents.state import StudyMateState
from app.agents.base import call_llm, truncate
from app.schemas import Flashcard

SYSTEM_PROMPT = """You are a study assistant that helps university students prepare for exams.
Your job is to create flashcards from lecture material.
Always respond with valid JSON."""

USER_PROMPT = """Read the following lecture text and create 10 to 15 flashcards for studying.

Rules:
- Each flashcard has a clear question on one side and a concise answer on the other.
- Questions should test understanding of key concepts, definitions, and facts.
- Answers should be complete but concise (1-3 sentences max).
- Cover a variety of topics from the text — don't repeat similar questions.
- Write in the same language as the lecture text.

Return ONLY a JSON object in this exact format:
{{
  "flashcards": [
    {{"question": "What is X?", "answer": "X is ..."}},
    {{"question": "What does Y mean?", "answer": "Y means ..."}}
  ]
}}

Lecture text:
{text}"""


async def flashcard_node(state: StudyMateState) -> dict:
    logger.info("FlashcardAgent: starting")

    try:
        data = await call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT.format(text=truncate(state["text"])),
        )
    except ValueError as e:
        logger.error(f"FlashcardAgent: LLM call failed, returning empty. Error: {e}")
        return {"flashcards": []}

    raw_cards: list[dict] = data.get("flashcards", [])

    flashcards: list[Flashcard] = []
    for item in raw_cards:
        try:
            flashcards.append(Flashcard(
                question=str(item.get("question", "")).strip(),
                answer=str(item.get("answer", "")).strip(),
            ))
        except Exception as e:
            logger.warning(f"Skipping malformed flashcard {item}: {e}")

    # Drop any cards where the LLM left a field empty
    flashcards = [fc for fc in flashcards if fc.question and fc.answer]

    logger.info(f"FlashcardAgent: done, {len(flashcards)} cards")
    return {"flashcards": flashcards}
