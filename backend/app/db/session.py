"""
Database engine + session factory.

Usage in route handlers / services:
    from app.db.session import get_db
    ...
    def my_route(db: Session = Depends(get_db)): ...

The `get_db` generator is the canonical FastAPI dependency for injecting a
database session.  It ensures the session is always closed, even on errors.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    # Connection pool tuning (overridable via config later)
    pool_pre_ping=True,        # cheap SELECT 1 before handing out a connection
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    echo=settings.db_echo,     # set True to log every SQL statement
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # avoid lazy-load surprises after commit
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee it is closed afterwards."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health helper
# ---------------------------------------------------------------------------
def check_db_connection() -> bool:
    """Return True if a simple SELECT 1 succeeds, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)
        return False
