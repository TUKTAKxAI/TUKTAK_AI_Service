from app.rag.document_loader import RiskDocument
from app.rag.risk_retriever import RiskDocumentRetriever


class LowSimilarityEmbeddingService:
    def embed_text(self, text):
        return [1.0, 0.0]

    def embed_texts(self, texts):
        return [[0.1, 0.0] for _ in texts]


def test_risk_retriever_returns_supporting_evidence_when_threshold_is_not_met() -> None:
    retriever = RiskDocumentRetriever(
        collection=None,
        embedding_service=LowSimilarityEmbeddingService(),
        documents=[
            RiskDocument(
                document_id="SAFETY_001",
                text="전기 작업은 감전 위험이 있어 차단기 확인이 필요하다.",
                metadata={
                    "document_id": "SAFETY_001",
                    "risk_category": "SAFETY",
                    "category": "전기",
                    "document_type": "SAFETY_GUIDE",
                    "source_file": "test.pdf",
                    "source_org": "테스트",
                    "service_task": "전기 수리",
                    "reliability_score": 0.9,
                },
            )
        ],
    )

    result = retriever.search({"main_category": "전기/조명", "repair_task": "콘센트 수리"}, "SAFETY")

    assert len(result) == 1
    assert result[0]["document_id"] == "SAFETY_001"
    assert result[0]["supporting_evidence"] is True
