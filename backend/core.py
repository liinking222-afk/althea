"""Shared core: DB client, env vars, llm key."""
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]


def is_budget_exceeded(exc: BaseException) -> bool:
    """Detect Emergent Universal Key budget-exhaustion errors so noisy
    autonomous loops can log a single warning instead of a full traceback."""
    msg = str(exc).lower()
    return (
        "budget has been exceeded" in msg
        or "budget_exceeded" in msg
        or ("max budget" in msg and "current cost" in msg)
    )

