"""
Database initialisation helpers.

Called once at application startup (via the FastAPI lifespan handler in main.py).

Responsibilities:
  1. Enable the pgvector extension (idempotent — IF NOT EXISTS).
  2. Create all tables that are not yet present in the database.
  3. Seed a default dev user if table is empty.
  4. Synchronize auto-increment sequences so new registrations never collide.
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
    """Enable pgvector, create missing tables, and sync sequences."""
    logger.info("Initialising database …")

    with engine.begin() as conn:
        # ------------------------------------------------------------------ #
        # 1. pgvector extension                                                #
        # ------------------------------------------------------------------ #
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension: ready")
        except Exception as exc:
            logger.warning("Could not create pgvector extension: %s", exc)

        # ------------------------------------------------------------------ #
        # 2. Schema (ORM-managed tables)                                       #
        # ------------------------------------------------------------------ #
        Base.metadata.create_all(bind=conn)
        logger.info("Database tables: up to date")

    # ------------------------------------------------------------------ #
    # 3. Dev seed — ensure default user exists                              #
    # ------------------------------------------------------------------ #
    _seed_dev_user()

    # ------------------------------------------------------------------ #
    # 4. Synchronize PostgreSQL sequences to avoid ID collision            #
    # ------------------------------------------------------------------ #
    _sync_sequences()

    logger.info("Database initialisation complete")


def _seed_dev_user() -> None:
    """Insert a placeholder user (id=1) if it doesn't exist yet with a valid password."""
    from app.core.security import hash_password
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        user = db.get(User, 1)
        if user is None:
            dev_user = User(
                id=1,
                email="dev@example.com",
                hashed_password=hash_password("password123"),
                is_active=True,
            )
            db.add(dev_user)
            db.commit()
            logger.info("Seeded dev user (id=1, email=dev@example.com, password=password123)")
    finally:
        db.close()


def _sync_sequences() -> None:
    """Ensure PostgreSQL autoincrement sequence is ahead of highest user ID."""
    with engine.begin() as conn:
        try:
            conn.execute(
                text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE(MAX(id), 1)) FROM users")
            )
        except Exception as exc:
            # SQLite or databases without sequence functions
            logger.debug("Sequence sync skipped: %s", exc)
