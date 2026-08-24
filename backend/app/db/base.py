"""
SQLAlchemy declarative base.

All ORM models must inherit from `Base` so that:
  - Alembic can auto-detect them for migrations
  - `Base.metadata.create_all()` can build the schema in tests / init_db
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy base class."""

    # Automatically derive __tablename__ from the class name (snake_case).
    # Individual models can still override __tablename__ explicitly.
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        import re
        # CamelCase  →  snake_case  (e.g. DocumentChunk → document_chunks)
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        # Append 's' only when the name doesn't already end in 's'
        return name if name.endswith("s") else name + "s"
