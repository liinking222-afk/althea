"""ALTHEA core — slim FastAPI app that wires routers."""
import logging
import sys
from pathlib import Path

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

# Allow flat module imports (core, models, utils, routers/*)
sys.path.insert(0, str(Path(__file__).parent))

from core import CORS_ORIGINS, mongo_client  # noqa: E402
from routers import (  # noqa: E402
    browser,
    chat,
    codegen,
    cognition,
    desktop,
    files,
    growth,
    lattice,
    memory,
    notifications,
    observe,
    perception,
    satellite,
    server_ops,
    system,
    web_bridge,
)


app = FastAPI(title="Althea AI Core")

api_router = APIRouter(prefix="/api")
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


@app.on_event("shutdown")
async def shutdown_db_client():
    mongo_client.close()
