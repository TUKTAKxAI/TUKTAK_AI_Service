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
    chroma_risk_document_collection: str = "risk_documents_ko_sroberta_v2"
    chroma_repair_manual_collection: str = "repair_manuals"
    chroma_price_reference_collection: str = "price_references"
    price_reference_file_path: str = "data/price_reference/base_price_table.csv"

    embedding_model_name: str = "BAAI/bge-m3"
    image_embedding_model_name: str = "nomic-ai/nomic-embed-vision-v1.5"

    nlp_structuring_model_name: str = "KLUE-RoBERTa-base"
    nlp_structuring_base_model_name: str = "klue/roberta-base"
    nlp_structuring_model_path: str = "data/models/KLUE-RoBERTa-base"
    nlp_structuring_hf_repo_id: str | None = None
    nlp_structuring_hf_revision: str | None = None
    nlp_structuring_hf_token: str | None = None
    nlp_structuring_auto_download: bool = True
    nlp_structuring_max_length: int = 192
    nlp_structuring_missing_threshold: float = 0.5

    openai_api_key: str | None = None
    openai_api_key_ai_estimate: str | None = None
    openai_api_key_ai_riskreport: str | None = None
    openai_estimate_model: str = "gpt-5-mini"
    openai_estimate_timeout_seconds: float = 60.0
    openai_risk_report_model: str = "gpt-5-mini"
    openai_risk_report_timeout_seconds: float = 60.0

    risk_embedding_model_name: str = "jhgan/ko-sroberta-multitask"
    risk_rag_metadata_path: str | None = "data/rag_documents/02_메타데이터/rag_documents_metadata_통합본.jsonl"
    risk_rag_top_k: int = 3
    risk_rag_price_threshold: float = 0.30
    risk_rag_extra_cost_threshold: float = 0.55
    risk_rag_safety_threshold: float = 0.60
    risk_rag_contract_threshold: float = 0.60
    risk_rag_field_threshold: float = 0.65

    aws_region: str = "ap-northeast-2"
    s3_bucket_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
