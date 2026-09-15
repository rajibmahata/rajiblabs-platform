"""MCP server configuration."""

from pydantic_settings import BaseSettings


class MCPSettings(BaseSettings):
    """MCP server settings loaded from environment variables."""

    # App
    app_name: str = "rajiblabs-mcp"
    app_env: str = "development"
    debug: bool = False

    # Database
    database_url: str = "mongodb://localhost:27017/rajiblabs"
    mongo_db_name: str = "rajiblabs"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "rajiblabs_knowledge"

    # GitHub
    github_owner: str = "rajib-mahata"
    github_token: str = ""

    # AI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # MCP Server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8100
    mcp_workers: int = 1

    # Auth
    mcp_api_key: str = ""
    admin_api_key: str = ""

    # Logging
    log_level: str = "INFO"

    # Observability
    enable_audit_log: bool = True
    enable_tool_metrics: bool = True

    model_config = {"env_prefix": "MCP_", "env_file": ".env"}


settings = MCPSettings()
