"""ALTHEA core — FastAPI app: auth, per-user tenancy, routers, worker mesh."""
from dotenv import load_dotenv

load_dotenv()

import logging  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

from fastapi import APIRouter, FastAPI, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

# Allow flat module imports (core, models, utils, routers/*)
sys.path.insert(0, str(Path(__file__).parent))

from auth import ensure_indexes, resolve_user, seed_founder  # noqa: E402
from core import CORS_ORIGINS, mongo_client, reset_tenant, set_tenant, shared_db  # noqa: E402
from migration import migrate_legacy_to_founder  # noqa: E402
from routers import (  # noqa: E402
    auth as auth_router,
    browser,
    chat,
    codegen,
    cognition,
    desktop,
    diagnostics,
    dm,
    evolution,
    files,
    growth,
    images,
    lattice,
    live_browser,
    memory,
    neural_interface,
    notifications,
    observe,
    perception,
    research,
    satellite,
    server_ops,
    synthesis,
    system,
    web_access,
    web_bridge,
    workers,
)

app = FastAPI(title="Althea AI Core")

PUBLIC_PATHS = {"/api/", "/api/health", "/api/auth/login", "/api/auth/register",
                "/api/auth/session", "/api/auth/logout"}
_last_seen_write: dict = {}


@app.middleware("http")
async def tenancy_middleware(request: Request, call_next):
    """Resolve the signed-in user once per request and scope every DB access
    to their private Althea. Everything under /api except auth is gated."""
    path = request.url.path
    if not path.startswith("/api") or request.method == "OPTIONS":
        return await call_next(request)
    user = await resolve_user(request)
    request.state.user = user
    if user is None:
        if path in PUBLIC_PATHS or path.startswith("/api/auth/"):
            return await call_next(request)
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    now = time.time()
    if now - _last_seen_write.get(user["user_id"], 0) > 60:
        _last_seen_write[user["user_id"]] = now
        await shared_db.users.update_one({"user_id": user["user_id"]},
                                         {"$set": {"last_seen": datetime.now(timezone.utc)}})
    token = set_tenant(user["user_id"])
    try:
        return await call_next(request)
    finally:
        reset_tenant(token)


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router.router)
api_router.include_router(dm.router)
api_router.include_router(chat.router)
api_router.include_router(memory.router)
api_router.include_router(observe.router)
api_router.include_router(cognition.router)
api_router.include_router(system.router)
api_router.include_router(lattice.router)
api_router.include_router(web_bridge.router)
api_router.include_router(perception.router)
api_router.include_router(growth.router)
api_router.include_router(notifications.router)
api_router.include_router(files.router)
api_router.include_router(browser.router)
api_router.include_router(server_ops.router)
api_router.include_router(satellite.router)
api_router.include_router(codegen.router)
api_router.include_router(desktop.router)
api_router.include_router(evolution.router)
api_router.include_router(diagnostics.router)
api_router.include_router(images.router)
api_router.include_router(workers.router)
api_router.include_router(synthesis.router)
api_router.include_router(web_access.router)
api_router.include_router(neural_interface.router)
api_router.include_router(live_browser.router)
api_router.include_router(research.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await ensure_indexes()
    founder = await seed_founder()
    if founder:
        await migrate_legacy_to_founder(founder["user_id"])
    workers.start_workers()


@app.on_event("shutdown")
async def shutdown_db_client():
    workers.stop_workers()
    mongo_client.close()
