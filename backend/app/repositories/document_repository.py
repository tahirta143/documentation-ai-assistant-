"""
Document repository — all raw DB access for the documents table.

Rules:
- No business logic here, only SQL / ORM queries.
- Every method receives a SQLAlchemy Session and returns ORM objects or None.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate


class DocumentRepository:
    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def create(self, db: Session, data: DocumentCreate) -> Document:
        doc = Document(
            user_id=data.user_id,
            filename=data.filename,
            file_type=data.file_type,
            file_path=data.file_path,
            file_size=data.file_size,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def update_status(self, db: Session, document_id: int, status: str) -> Document | None:
        doc = self.get_by_id(db, document_id)
        if doc is None:
            return None
        doc.status = status
        db.commit()
        db.refresh(doc)
        return doc

    def delete(self, db: Session, document_id: int) -> bool:
        doc = self.get_by_id(db, document_id)
        if doc is None:
            return False
        db.delete(doc)
        db.commit()
        return True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_by_id(self, db: Session, document_id: int) -> Document | None:
        return db.get(Document, document_id)

    def list_by_user(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Document]]:
        """Return (total_count, page_of_documents) for a given user."""
        base_q = select(Document).where(Document.user_id == user_id)

        total: int = db.execute(
            select(func.count()).select_from(base_q.subquery())
        ).scalar_one()

        items: list[Document] = list(
            db.execute(
                base_q.order_by(Document.created_at.desc()).offset(skip).limit(limit)
            ).scalars()
        )
        return total, items


# Module-level singleton — import and use directly in services.
document_repository = DocumentRepository()
