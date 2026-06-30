from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = (
        "postgresql+asyncpg://platform:platform@localhost:5432/platform"
    )

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_raw: str = "raw"
    minio_bucket_processed: str = "processed"
    minio_bucket_curated: str = "curated"
    minio_secure: bool = False

    genomics_ref_dir: str = "/ref"
    genomics_workspace: str = "/workspace"
    genomics_pipeline_dir: str = "/pipeline"
    genomics_worker_container: str = "03-genomica-worker-1"
    genomics_default_profile: str = "docker"

    max_concurrent_runs: int = 2

    datalake_api_url: str = "http://api-data-lake:8000"

    domain: str = "localhost"

    log_level: str = "INFO"


settings = Settings()
