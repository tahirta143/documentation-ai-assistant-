"""
Shared FastAPI dependencies.

Import and use with Depends() in route handlers:

    from app.api.v1.deps import get_db
    ...
    def my_route(db: Session = Depends(get_db)): ...
"""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
