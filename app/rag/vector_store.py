from app.core.config import settings


def get_chroma_settings() -> dict[str, str]:
    return {
        "path": settings.chroma_path,
        "repair_cases": settings.chroma_repair_case_collection,
        "risk_documents": settings.chroma_risk_document_collection,
        "repair_manuals": settings.chroma_repair_manual_collection,
        "price_references": settings.chroma_price_reference_collection,
    }

