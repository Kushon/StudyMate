import json
import re
from openai import AsyncOpenAI
from loguru import logger
from app.config import OLLAMA_BASE_URL, OLLAMA_API_KEY, LLM_MODEL

def _extract_json(text: str) -> dict:
    """
    Try to parse JSON from the model's raw output.
    Handles three common cases:
      1. Pure JSON response
      2. JSON wrapped in a ```json ... ``` code fence
      3. JSON embedded somewhere in prose text
    """
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fence
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Find the outermost {...} block in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


# Single shared async client — reused across all agents
client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)

# Truncate input so very long lectures don't blow up latency.
# gemma3:4b has a 128k context, but we cap at ~12k chars (~3k tokens)
# to keep responses fast during development.
MAX_INPUT_CHARS = 12_000


def truncate(text: str) -> str:
    if len(text) <= MAX_INPUT_CHARS:
        return text
    logger.warning(f"Text truncated from {len(text)} to {MAX_INPUT_CHARS} chars")
    return text[:MAX_INPUT_CHARS] + "\n\n[... text truncated ...]"


async def call_llm(system_prompt: str, user_prompt: str, retries: int = 2) -> dict:
    """
    Send a chat completion request to Ollama and return parsed JSON.
    Retries on empty or invalid JSON responses (Ollama can drop output under load).
    Raises ValueError if all attempts fail.
    """
    last_error: Exception = ValueError("No attempts made")

    for attempt in range(1, retries + 1):
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                # No response_format — gemma3 returns {} for complex prompts under that constraint.
                # We extract JSON from the raw text instead.
            )

            raw = response.choices[0].message.content or ""
            logger.debug(f"LLM raw response ({len(raw)} chars): {raw[:200]}...")

            data = _extract_json(raw)

            # Treat a completely empty object as a failed attempt
            if not data:
                raise ValueError("LLM returned empty JSON object {}")

            return data

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{retries} failed: {e}. Retrying...")

    logger.error(f"All {retries} attempts failed. Last error: {last_error}")
    raise ValueError(f"LLM failed after {retries} attempts: {last_error}")
