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
    diagnostics,
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
async def start_background_workers():
    workers.start_workers()


@app.on_event("shutdown")
async def shutdown_db_client():
    workers.stop_workers()
    mongo_client.close()
