"""Application settings, loaded from environment variables (and a local .env file).

Centralising configuration here means the rest of the code never reads os.environ
directly — it asks for `settings.<field>`, which is typed and validated once.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Persistence
    database_url: str = "postgresql+psycopg://assistai:assistai@localhost:5433/assistai"
    redis_url: str = "redis://localhost:6379/0"

    # Embeddings: the vector length stored in the `chunk` table. Must match the
    # embedding model used during ingestion.
    embedding_dim: int = 1024

    # CORS: which browser origins may call the API. Comma-separated in the env var.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
