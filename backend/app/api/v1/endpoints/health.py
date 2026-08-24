from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.db.session import check_db_connection

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    app: str
    database: str


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    db_ok = check_db_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        app=settings.app_name,
        database="connected" if db_ok else "unreachable",
    )
