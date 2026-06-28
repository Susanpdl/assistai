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

    # --- URLs ---
    # Where the backend is reachable (magic-link points here, at /auth/verify).
    api_base_url: str = "http://localhost:8000"
    # Where to send the user after a successful login.
    frontend_url: str = "http://localhost:5173"

    # --- Auth: magic link + sessions ---
    # How long a magic-link token is valid, in minutes.
    token_ttl_minutes: int = 15
    # How long a login session lasts, in days (our "remember me" default).
    session_ttl_days: int = 14
    # The session cookie. `secure=True` only over HTTPS (so keep False in local dev).
    session_cookie_name: str = "assistai_session"
    session_cookie_secure: bool = False
    # Comma-separated allowlist of emails that become `instructor` on first login;
    # everyone else becomes `student`.
    instructor_emails: str = ""
    # Rate limit for POST /auth/request: max requests per email (and per IP) per window.
    auth_request_max_per_window: int = 5
    auth_request_window_minutes: int = 15

    # --- Email provider ---
    # "console" logs the magic link to stdout (dev). "resend" sends real email.
    email_backend: str = "console"
    email_from: str = "AssistAI <login@assistai.local>"
    resend_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def instructor_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.instructor_emails.split(",") if e.strip()}


settings = Settings()
