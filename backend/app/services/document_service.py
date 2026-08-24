"""
Document service — business logic for document management.

Responsibilities:
- Validate file type and size.
- Save the uploaded file to disk.
- Insert a row in the documents table (status = processing).
- Trigger the ingestion pipeline (extract → chunk → store chunks).
- Delete file from disk when a document is deleted from DB.
"""

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.repositories.document_repository import document_repository
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "md", "txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/plain",
    "text/x-markdown",
}


class DocumentService:
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validate_file(self, file: UploadFile) -> str:
        """Validate extension + size. Returns the lowercased extension."""
        name = file.filename or ""
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '.{ext}' is not supported. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
            )
        return ext

    def _save_to_disk(self, file: UploadFile, ext: str) -> tuple[Path, int]:
        """Write the upload to the uploads directory. Returns (path, size_bytes)."""
        upload_dir: Path = settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Use a UUID filename to avoid collisions
        dest = upload_dir / f"{uuid.uuid4()}.{ext}"
        content = file.file.read()

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB.",
            )

        dest.write_bytes(content)
        logger.info("Saved upload to %s (%d bytes)", dest, len(content))
        return dest, len(content)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def upload(
        self,
        db: Session,
        file: UploadFile,
        user_id: int = 1,  # placeholder until auth is wired (Phase 14)
    ) -> DocumentResponse:
        ext = self._validate_file(file)
        dest, size = self._save_to_disk(file, ext)

        data = DocumentCreate(
            filename=file.filename or dest.name,
            file_type=ext,
            file_path=str(dest),
            file_size=size,
            user_id=user_id,
        )
        doc = document_repository.create(db, data)
        logger.info("Created document id=%d status=%s", doc.id, doc.status)

        # Phase 6: full ingestion pipeline (extract → chunk → store)
        from app.services.ingestion_service import ingestion_service
        ingestion_service.ingest(db, doc)

        return DocumentResponse.model_validate(doc)

    def get_by_id(self, db: Session, document_id: int) -> DocumentResponse:
        doc = document_repository.get_by_id(db, document_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )
        return DocumentResponse.model_validate(doc)

    def list_documents(
        self,
        db: Session,
        user_id: int = 1,
        skip: int = 0,
        limit: int = 50,
    ) -> DocumentListResponse:
        total, items = document_repository.list_by_user(db, user_id, skip, limit)
        return DocumentListResponse(
            total=total,
            items=[DocumentResponse.model_validate(d) for d in items],
        )

    def delete(self, db: Session, document_id: int) -> None:
        doc: Document | None = document_repository.get_by_id(db, document_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )
        # Remove file from disk (best-effort)
        try:
            Path(doc.file_path).unlink(missing_ok=True)
            logger.info("Deleted file %s", doc.file_path)
        except Exception as exc:
            logger.warning("Could not delete file %s: %s", doc.file_path, exc)

        document_repository.delete(db, document_id)
        logger.info("Deleted document id=%d", document_id)


document_service = DocumentService()
