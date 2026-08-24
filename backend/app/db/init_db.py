"""
Database initialisation helpers.

Called once at application startup (via the FastAPI lifespan handler in main.py).

Responsibilities:
  1. Enable the pgvector extension (idempotent — IF NOT EXISTS).
  2. Create all tables that are not yet present in the database.
     (In production you should use Alembic migrations instead; this is a
     convenience for development / first-run bootstrapping.)
"""

import logging

from sqlalchemy import text

from app.db.base import Base  # noqa: F401 — triggers model registration
from app.db.session import engine

# Import every model so their classes are registered on Base.metadata
# before create_all() is called.
from app.models import Conversation, Document, DocumentChunk, Message, User  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Enable pgvector and create missing tables."""
    logger.info("Initialising database …")

    with engine.begin() as conn:
        # ------------------------------------------------------------------ #
        # 1. pgvector extension                                                #
        # ------------------------------------------------------------------ #
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension: ready")
        except Exception as exc:
            # The extension may already exist or the user may lack superuser
            # rights — log a warning but don't crash the app.
            logger.warning("Could not create pgvector extension: %s", exc)

        # ------------------------------------------------------------------ #
        # 2. Schema (ORM-managed tables)                                       #
        # ------------------------------------------------------------------ #
        Base.metadata.create_all(bind=conn)
        logger.info("Database tables: up to date")

    # ------------------------------------------------------------------ #
    # 3. Dev seed — ensure a default user exists for pre-auth testing      #
    # ------------------------------------------------------------------ #
    _seed_dev_user()

    logger.info("Database initialisation complete")


def _seed_dev_user() -> None:
    """Insert a placeholder user (id=1) if it doesn't exist yet.

    Development convenience only — replaced once real auth (Phase 14) is wired in.
    """
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.get(User, 1)
        if user is None:
            dev_user = User(
                id=1,
                email="dev@example.com",
                hashed_password="dev_placeholder",
                is_active=True,
            )
            db.add(dev_user)
            db.commit()
            logger.info("Seeded dev user (id=1, email=dev@example.com)")
    finally:
        db.close()
