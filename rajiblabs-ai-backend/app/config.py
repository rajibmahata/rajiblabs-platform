"""Application configuration loaded from environment / .env file (MongoDB, not SQLite)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"  # development | production
    app_url: str = "https://rajiblabs.com"
    app_timezone: str = "Asia/Kolkata"
    base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173,https://rajiblabs.com"
    secret_key: str = "dev-secret-change-me-32-chars-min"

    # Database — MongoDB (per project decision, not SQLite)
    database_url: str = "mongodb://localhost:27017/rajiblabs"
    mongo_db_name: str = "rajiblabs"

    # Admin seed (used only on first run; never overwrite existing)
    admin_emails: str = "rajibmahata143@gmail.com,rajibmahata143@outlook.com"
    admin_initial_password: str = ""

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 15
    refresh_expire_days: int = 7
    jwt_issuer: str = "rajiblabs"

    # OpenAI (server-only)
    openai_api_key: str = ""
    openai_model: str = "gpt-5-nano"
    # One-shot fallback when the primary model 404s (unknown/inaccessible).
    # gpt-5.6-luna is real (GPT-5.6 cheap tier, $0.20/$1.20) — higher quality
    # than nano for the fallback path. Override via env if needed.
    openai_fallback_model: str = "gpt-5.6-luna"
    openai_enabled: bool = True
    openai_max_retries: int = 3
    ai_auto_publish: bool = False
    ai_quality_threshold: int = 85

    # Lead-assistant AI provider (server-only, never exposed to React).
    # ai_provider: "openai" | "deepseek". ai_model empty = provider default
    # (openai_model for OpenAI). Fallback chain + retries keep chat resilient.
    ai_provider: str = "openai"
    ai_model: str = ""
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    ai_fallback_enabled: bool = True

    # AI provider abstraction for the lead assistant (server-only).
    # ai_provider: "openai" | "deepseek". ai_model empty = provider default
    # (openai_model for OpenAI). Fallback chain + retries keep chat resilient.
    ai_provider: str = "openai"
    ai_model: str = ""
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    ai_fallback_enabled: bool = True

    # GitHub (server-only)
    github_owner: str = "rajibmahata"
    github_token: str = ""
    github_sync_enabled: bool = True

    # Agent / chat
    daily_agent_enabled: bool = True
    daily_agent_hour: int = 2
    daily_agent_minute: int = 0
    chat_enabled: bool = True

    # Contact (centralized, mirrors frontend site.ts)
    contact_email: str = "rajibmahata143@gmail.com"
    contact_email_secondary: str = "rajibmahata143@outlook.com"
    primary_phone: str = "+918420249020"
    secondary_phone: str = "+919100184730"
    whatsapp_phone: str = "+918420249020"

    # Uploads
    upload_dir: str = "./data/uploads"
    resume_path: str = ""
    max_image_mb: int = 5
    max_resume_mb: int = 10

    # Failure logs (admin-visible, auto-expire)
    log_retention_days: int = 7

    # Agent API key (X-Api-Key for /api/activity POST + /api/projects PATCH).
    # Empty = unchecked, same as the legacy .NET RequireApiKey behavior.
    api_key: str = ""

    # RAG knowledge system (Qdrant vector search; MongoDB stays source of truth)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "rajiblabs_knowledge"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_version: str = "v1"
    embedding_dim: int = 1536
    rag_enabled: bool = True
    rag_top_k: int = 5
    rag_min_score: float = 0.35
    rag_cache_ttl_seconds: int = 3600
    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 150
    github_rag_repos: str = ""  # comma-separated allowlist; empty = all public
    github_rag_max_files: int = 40
    github_rag_max_bytes: int = 200000

    # SMTP (optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    def is_openai_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_enabled)

    def is_github_configured(self) -> bool:
        return bool(self.github_token and self.github_sync_enabled)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.app_env == "production":
        missing = [k for k in ("secret_key", "jwt_secret") if not getattr(s, k) or "change-me" in getattr(s, k)]
        if missing:
            raise RuntimeError(f"Missing critical settings in production: {missing}")
    return s
