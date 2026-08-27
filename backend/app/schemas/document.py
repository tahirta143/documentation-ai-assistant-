from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int | None = None


class DocumentUrlRequest(BaseModel):
    url: str


class DocumentCreate(DocumentBase):
    """Used internally by the service after saving the file."""
    file_path: str
    user_id: int


class DocumentResponse(DocumentBase):
    """Returned to the client."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    file_path: str
    status: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    """Paginated list wrapper."""
    total: int
    items: list[DocumentResponse]
