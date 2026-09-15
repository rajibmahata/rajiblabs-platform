from pydantic_settings import BaseSettings


class MCPSettings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = "mongodb://localhost:27017/rajiblabs"
    MONGO_DB_NAME: str = "rajiblabs"

    QDRANT_URL: str = "http://localhost:6333"

    REDIS_URL: str = "redis://localhost:6379/0"

    GITHUB_OWNER: str = "rajibmahata"
    GITHUB_TOKEN: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    MCP_HOST: str = "0.0.0.0"
    MCP_PORT: int = 8100
    MCP_TRANSPORT: str = "sse"

    MCP_API_KEY: str = ""
    ADMIN_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_TOOL_METRICS: bool = True

    CACHE_TTL_SECONDS: int = 300
    CACHE_ENABLED: bool = True

    model_config = {"env_prefix": "MCP_", "env_file": ".env", "extra": "ignore"}


settings = MCPSettings()
