import logging

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    logger.info("Started %s in %s mode", settings.app_name, settings.environment)
    return app


app = create_app()
