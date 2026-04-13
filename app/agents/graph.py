import asyncio
from loguru import logger
from app.agents.state import StudyMateState
from app.agents.summary import summary_node
from app.agents.flashcard import flashcard_node
from app.agents.quiz import quiz_node


async def run_graph(text: str) -> StudyMateState:
    """
    Orchestrator: runs all three agents in parallel and merges their results.

    LangGraph's built-in parallel fan-out requires sync nodes; we use
    asyncio.gather here to keep everything async and add LangGraph's
    StateGraph wiring in Phase 3 once agents are real.
    """
    logger.info("Orchestrator: running agents in parallel")

    initial_state: StudyMateState = {
        "text": text,
        "summary": [],
        "flashcards": [],
        "quiz": [],
    }

    summary_result, flashcard_result, quiz_result = await asyncio.gather(
        summary_node(initial_state),
        flashcard_node(initial_state),
        quiz_node(initial_state),
    )

    final_state: StudyMateState = {
        **initial_state,
        **summary_result,
        **flashcard_result,
        **quiz_result,
    }

    logger.info("Orchestrator: all agents done")
    return final_state
