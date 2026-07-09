from fastapi import APIRouter

from app.core.config import settings
from app.schemas.rag import RagDocumentRequest, RagDocumentResponse

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/documents", response_model=RagDocumentResponse)
async def ingest_document(payload: RagDocumentRequest) -> RagDocumentResponse:
    return RagDocumentResponse(
        success=True,
        document_id=payload.document_id,
        status="accepted",
        message="문서 수집 API 형태만 먼저 고정했습니다. 파싱/임베딩은 다음 단계에서 연결합니다.",
    )


@router.get("/collections")
async def list_collections() -> dict[str, list[str]]:
    return {
        "collections": [
            settings.chroma_repair_case_collection,
            settings.chroma_risk_document_collection,
            settings.chroma_repair_manual_collection,
            settings.chroma_price_reference_collection,
        ]
    }

