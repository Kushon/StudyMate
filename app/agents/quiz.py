from loguru import logger
from app.agents.state import StudyMateState
from app.agents.base import call_llm, truncate
from app.schemas import QuizQuestion

SYSTEM_PROMPT = """You are a study assistant that helps university students prepare for exams.
Your job is to create multiple choice quiz questions from lecture material.
Always respond with valid JSON."""

USER_PROMPT = """Read the following lecture text and create 5 to 8 multiple choice questions.

Rules:
- Each question must have exactly 4 answer options.
- Only one option is correct; the other three are plausible but wrong.
- correct_index is the 0-based index of the correct option in the "options" array.
- explanation should briefly explain why the correct answer is right.
- Write in the same language as the lecture text.

Return ONLY a JSON object in this exact format:
{{
  "quiz": [
    {{
      "question": "Which of the following best describes X?",
      "options": ["Correct answer", "Wrong option B", "Wrong option C", "Wrong option D"],
      "correct_index": 0,
      "explanation": "X is best described as ... because ..."
    }}
  ]
}}

Lecture text:
{text}"""


async def quiz_node(state: StudyMateState) -> dict:
    logger.info("QuizAgent: starting")

    try:
        data = await call_llm(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT.format(text=truncate(state["text"])),
        )
    except ValueError as e:
        logger.error(f"QuizAgent: LLM call failed, returning empty quiz. Error: {e}")
        return {"quiz": []}

    raw_questions: list[dict] = data.get("quiz", [])

    quiz: list[QuizQuestion] = []
    for item in raw_questions:
        try:
            options = item.get("options", [])
            correct_index = int(item.get("correct_index", 0))

            if len(options) != 4:
                logger.warning(f"Skipping question with {len(options)} options (expected 4): {item.get('question')}")
                continue
            if not (0 <= correct_index <= 3):
                logger.warning(f"Skipping question with out-of-range correct_index {correct_index}")
                continue

            quiz.append(QuizQuestion(
                question=str(item.get("question", "")).strip(),
                options=[str(o).strip() for o in options],
                correct_index=correct_index,
                explanation=str(item.get("explanation", "")).strip(),
            ))
        except Exception as e:
            logger.warning(f"Skipping malformed quiz question {item}: {e}")

    # Drop questions with empty text
    quiz = [q for q in quiz if q.question and q.explanation]

    logger.info(f"QuizAgent: done, {len(quiz)} questions")
    return {"quiz": quiz}
