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
    openai_fallback_model: str = "gpt-5.6-luna"
    openai_enabled: bool = True
    openai_max_retries: int = 3
    ai_auto_publish: bool = False
    ai_quality_threshold: int = 85

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
