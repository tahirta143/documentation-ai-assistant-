import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: runs once on startup and once on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # --- startup ---
    logger.info("Starting up %s …", settings.app_name)
    from app.db.init_db import init_db
    init_db()

    yield  # application is running

    # --- shutdown ---
    logger.info("Shutting down %s …", settings.app_name)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Mount frontend static files — serves index.html, CSS, JS at /static/
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir), html=True), name="static")
        logger.info("Mounted frontend from %s", frontend_dir)
    else:
        logger.warning("Frontend directory not found at %s", frontend_dir)

    logger.info("Started %s in %s mode", settings.app_name, settings.environment)
    return app


app = create_app()
