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
    # Which embedder to use. "local" is a deterministic, offline, hashing-based embedder
    # for dev/tests (no API key); a real provider (e.g. Voyage) is wired in Phase 4.
    embedding_backend: str = "local"

    # --- Content ingestion (Phase 3) ---
    # Where uploaded course files are stored. "local" writes to `storage_dir`; this is the
    # object-storage seam — a future "s3" backend slots in here without touching callers.
    storage_backend: str = "local"
    storage_dir: str = "./storage"
    # Reject uploads larger than this (megabytes) or with a disallowed extension.
    max_upload_mb: int = 20
    allowed_upload_extensions: str = "pdf,docx,pptx,txt,md"
    # Redis list that the ingestion worker pulls document ids from.
    ingest_queue_key: str = "assistai:ingest"
    # Chunking defaults (~500 tokens / ~50 overlap, approximated by characters).
    chunk_chars: int = 2000
    chunk_overlap_chars: int = 200

    # --- AI Tutor (Phase 4) ---
    # Which generator to use. "local" is a deterministic, offline, extractive generator
    # (dev/tests, no API key, zero cost). "claude" calls the Anthropic API.
    generation_backend: str = "local"
    anthropic_api_key: str = ""
    # The Claude model for grounded generation when generation_backend == "claude".
    tutor_model: str = "claude-sonnet-4-6"
    tutor_max_tokens: int = 1024
    # How many chunks to retrieve as context for an answer.
    tutor_top_k: int = 4
    # Minimum cosine similarity (0..1) for the best chunk to count as "relevant". Below
    # this we don't invent an answer — we say we're unsure and escalate to the instructor.
    tutor_min_similarity: float = 0.05

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

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            e.strip().lower().lstrip(".")
            for e in self.allowed_upload_extensions.split(",")
            if e.strip()
        }


settings = Settings()
