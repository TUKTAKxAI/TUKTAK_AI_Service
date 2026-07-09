from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TukTak AI Service"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    debug: bool = True

    main_backend_url: str = "http://localhost:8081"

    chroma_path: str = "./data/chroma"
    chroma_repair_case_collection: str = "repair_cases"
    chroma_risk_document_collection: str = "risk_documents"

    embedding_model_name: str = "BAAI/bge-m3"

    openai_api_key: str | None = None

    aws_region: str = "ap-northeast-2"
    s3_bucket_name: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()