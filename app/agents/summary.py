from loguru import logger
from app.agents.state import StudyMateState
from app.agents.base import call_llm, truncate

SYSTEM_PROMPT = """You are a study assistant that helps university students prepare for exams.
Your job is to read lecture material and extract the most important thesis points.
Always respond with valid JSON."""

USER_PROMPT = """Read the following lecture text and extract 7 to 10 key thesis points.

Rules:
- Each point must be a complete, informative sentence (not a heading or single word).
- Focus on definitions, key concepts, and important facts a student should know.
- Write in the same language as the lecture text.

Return ONLY a JSON object in this exact format:
{{
  "points": [
    "First key thesis point as a full sentence.",
    "Second key thesis point as a full sentence.",
    ...
  ]
}}

Lecture text:
{text}"""


async def summary_node(state: StudyMateState) -> dict:
    logger.info("SummaryAgent: starting")

    try:
        data = await call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT.format(text=truncate(state["text"])),
        )
    except ValueError as e:
        logger.error(f"SummaryAgent: LLM call failed, returning empty. Error: {e}")
        return {"summary": []}

    points: list[str] = data.get("points", [])

    # Defensive: filter out empty strings
    points = [p.strip() for p in points if isinstance(p, str) and p.strip()]

    logger.info(f"SummaryAgent: done, {len(points)} points")
    return {"summary": points}
