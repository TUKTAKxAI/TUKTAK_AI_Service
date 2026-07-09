from app.core.config import settings


def get_embedding_model_name() -> str:
    return settings.embedding_model_name

