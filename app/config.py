import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")  # Ollama ignores this but the SDK requires it
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./studymate.db")

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
