"""
Document endpoints.

POST   /api/documents/upload  — upload a PDF / MD / TXT file
GET    /api/documents          — list all documents for the current user
GET    /api/documents/{id}     — get a single document by ID
DELETE /api/documents/{id}     — delete a document + its file from disk
"""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document (PDF, Markdown, or plain text)",
)
def upload_document(
    file: UploadFile = File(..., description="PDF, .md, or .txt file"),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a document for processing.

    - Accepts: `.pdf`, `.md`, `.txt`
    - Max size: configured via `MAX_UPLOAD_SIZE_MB` (default 25 MB)
    - The document is saved to disk and a DB row is created with `status = processing`.
    - Embedding happens asynchronously in a later phase.
    """
    return document_service.upload(db=db, file=file)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents",
)
def list_documents(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """Return a paginated list of documents for the current user."""
    return document_service.list_documents(db=db, skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a document by ID",
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Fetch a single document record by its ID."""
    return document_service.get_by_id(db=db, document_id=document_id)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its file",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a document record from the database and remove its file from disk.
    Also cascades to all associated chunks (via DB FK cascade).
    """
    document_service.delete(db=db, document_id=document_id)
