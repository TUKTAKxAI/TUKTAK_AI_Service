from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    app_name: str = "TukTak AI Service"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    debug: bool = True

    main_backend_url: str = "http://localhost:8000"

    chroma_path: str = "./data/chroma"
    chroma_repair_case_collection: str = "repair_cases"
    chroma_risk_document_collection: str = "risk_documents"
    chroma_repair_manual_collection: str = "repair_manuals"
    chroma_price_reference_collection: str = "price_references"
    price_reference_file_path: str = "data/price_reference/base_price_table.sample.csv"

    embedding_model_name: str = "BAAI/bge-m3"

    nlp_structuring_model_name: str = "KLUE-RoBERTa-base"
    nlp_structuring_base_model_name: str = "klue/roberta-base"
    nlp_structuring_model_path: str = "data/models/KLUE-RoBERTa-base"
    nlp_structuring_max_length: int = 192
    nlp_structuring_missing_threshold: float = 0.5

    openai_api_key: str | None = None

    aws_region: str = "ap-northeast-2"
    s3_bucket_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "debug", "local", "dev", "development"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
                return False
        return value


settings = Settings()
