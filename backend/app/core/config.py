from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Andromeda — Enterprise AI Agent Platform"
    database_url: str = Field(
        default="sqlite:///./data/andromeda.db"
    )
    business_today: str = "2025-01-15"
    frontend_origin: str = "http://localhost:3000"

    llm_provider: str = Field(default="gemini", pattern="^(gemini|groq|openai|mock)$")
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # RAG / ChromaDB (Phase 3)
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    rag_enabled: bool = False
    rag_top_k: int = 3
    rag_score_threshold: float = 0.65
    embedding_provider: str = "local"  # "local" | "openai"

    # Observability (Phase 5)
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Agent mode
    tool_mode: str = "local"       # "local" | "mcp"
    agent_mode: str = "graph"      # "graph" | "legacy"
    agent_architecture: str = "single"  # "single" | "multi"

    seed_data_path: Path = Path(__file__).resolve().parents[1] / "data" / "synthetic_crm.json"
    policy_path: Path = Path(__file__).resolve().parents[1] / "data" / "andromeda_refund_policy.md"


@lru_cache
def get_settings() -> Settings:
    return Settings()
