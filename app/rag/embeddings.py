from functools import lru_cache

from app.core.config import settings
from app.services.torch_device import select_torch_device


def get_embedding_model_name() -> str:
    return settings.embedding_model_name


class RiskEmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.risk_embedding_model_name
        self._model = None

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [embedding.astype("float32").tolist() for embedding in embeddings]

    def _get_model(self):
        if self._model is None:
            try:
                import torch
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("sentence-transformers is required for risk RAG embeddings.") from exc
            device = str(select_torch_device(torch))
            self._model = SentenceTransformer(self.model_name, device=device)
        return self._model


@lru_cache(maxsize=1)
def get_risk_embedding_service() -> RiskEmbeddingService:
    return RiskEmbeddingService()
