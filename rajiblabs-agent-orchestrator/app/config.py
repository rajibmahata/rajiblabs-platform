from pydantic_settings import BaseSettings


class OrchestratorSettings(BaseSettings):
    APP_ENV: str = "development"

    DATABASE_URL: str = "mongodb://localhost:27017/rajiblabs"
    MONGO_DB_NAME: str = "rajiblabs"

    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379/0"

    MCP_URL: str = "http://localhost:8100"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""

    MAX_DEPTH: int = 10
    MAX_ITERATIONS: int = 20
    MAX_TOKENS: int = 100000
    TIMEOUT_SECONDS: int = 300
    RETRY_LIMIT: int = 3

    COST_PER_1K_INPUT: float = 0.00015
    COST_PER_1K_OUTPUT: float = 0.0006

    LOG_LEVEL: str = "INFO"

    model_config = {"env_prefix": "ORCH_", "env_file": ".env", "extra": "ignore"}


settings = OrchestratorSettings()
