"""Shared core: DB client, env vars, llm key, per-user tenancy.

Every signed-in user owns a fully separate Althea. Tenancy is implemented
as a collection-prefix proxy: inside a request (or a worker tick) the
current tenant is held in a ContextVar and `db.<collection>` transparently
resolves to `<prefix>__<collection>`. Shared, cross-user data (accounts,
sessions, direct-message rooms) lives in `shared_db`.
"""
import os
from contextvars import ContextVar
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
shared_db = mongo_client[DB_NAME]

_tenant: ContextVar[str] = ContextVar("althea_tenant", default="")
GROWN_ROOT = Path("/app/althea_grown_code")


def set_tenant(tenant: str):
    """Returns a token; pass it to reset_tenant() when leaving the scope."""
    return _tenant.set(tenant or "")


def reset_tenant(token):
    _tenant.reset(token)


def current_tenant() -> str:
    return _tenant.get()


def tenant_collection_name(name: str, tenant: str = None) -> str:
    t = _tenant.get() if tenant is None else tenant
    return f"{t}__{name}" if t else name


class _TenantDB:
    """Drop-in for a Motor database: attribute/item access yields the
    current tenant's collection. No tenant → legacy un-prefixed names."""

    def __getattr__(self, name: str):
        return shared_db[tenant_collection_name(name)]

    def __getitem__(self, name: str):
        return shared_db[tenant_collection_name(name)]


db = _TenantDB()


def grown_code_dir() -> Path:
    """Per-tenant directory for self-grown code modules."""
    t = _tenant.get()
    path = GROWN_ROOT / t if t else GROWN_ROOT
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return path


def is_budget_exceeded(exc: BaseException) -> bool:
    """Detect Emergent Universal Key budget-exhaustion errors so noisy
    autonomous loops can log a single warning instead of a full traceback."""
    msg = str(exc).lower()
    return (
        "budget has been exceeded" in msg
        or "budget_exceeded" in msg
        or ("max budget" in msg and "current cost" in msg)
    )
