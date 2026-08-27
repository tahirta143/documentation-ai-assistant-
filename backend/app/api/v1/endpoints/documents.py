"""
Document endpoints (Secured with JWT authentication).

POST   /api/documents/upload  — upload a PDF / MD / TXT file
POST   /api/documents/url     — scrape and ingest a web URL
GET    /api/documents          — list all documents for the current user
GET    /api/documents/{id}     — get a single document by ID
DELETE /api/documents/{id}     — delete a document + its file from disk
"""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUrlRequest,
)
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
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """
    Upload a document for processing.
    The document is saved to disk, chunked, embedded, and scoped to current_user.
    """
    return document_service.upload(db=db, file=file, user_id=current_user.id)


@router.post(
    "/url",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Scrape and ingest documentation from a web URL",
)
def ingest_url(
    payload: DocumentUrlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """
    Scrape a web page, extract main text, chunk, embed, and store scoped to current_user.
    """
    return document_service.upload_url(db=db, url=payload.url, user_id=current_user.id)


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded documents for current user",
)
def list_documents(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """Return a paginated list of documents belonging to the authenticated user."""
    return document_service.list_documents(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a document by ID",
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Fetch a single document record by its ID."""
    return document_service.get_by_id(
        db=db, document_id=document_id, user_id=current_user.id
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its file",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a document record and remove its file from disk.
    Cascades to all associated chunks.
    """
    document_service.delete(
        db=db, document_id=document_id, user_id=current_user.id
    )
