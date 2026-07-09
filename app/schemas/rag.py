from pydantic import BaseModel


class RagDocumentRequest(BaseModel):
    document_id: str
    title: str
    source_url: str | None = None
    content: str | None = None
    collection_name: str | None = None


class RagDocumentResponse(BaseModel):
    success: bool
    document_id: str
    status: str
    message: str

