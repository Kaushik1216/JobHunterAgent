from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JOB_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # LLM / SLM Provider (supports "lm_studio", "ollama", "openai")
    llm_provider: Literal["lm_studio", "ollama", "openai"] = "lm_studio"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "qwen2.5-7b-instruct"
    llm_temperature: float = 0.0
    llm_timeout: int = 180
    llm_max_retries: int = 3
    
    # Ollama compatibility fields
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    ollama_temperature: float = 0.0
    ollama_timeout: int = 180
    ollama_max_retries: int = 3
    
    # Search
    search_jitter_min: float = 0.5
    search_jitter_max: float = 1.0
    search_max_results: int = 5
    search_circuit_breaker_threshold: int = 3
    search_circuit_breaker_cooldown: int = 60
    # Comma-separated portal ids from job_agent.portals.PORTAL_REGISTRY
    search_portals: str = "linkedin,indeed,naukri,greenhouse,lever"
    search_max_days: int = 7 # Controls DuckDuckGo timelimit (d, w, m, y)

    def enabled_portal_ids(self) -> list[str]:
        return [portal_id.strip().lower() for portal_id in self.search_portals.split(",") if portal_id.strip()]
    
    # Evaluation
    fit_score_threshold: float = 0.70
    
    # Paths
    db_path: Path = Path(__file__).parent.parent.parent / "jobs_vault.db"
    criteria_path: Path = Path(__file__).parent.parent.parent / "criteria.yaml"
    jd_path: Path = Path(__file__).parent.parent.parent / "job_description.txt"
    output_path: Path = Path(__file__).parent.parent.parent / "jobs_output.md"
    
    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"
    
    # Dashboard (FastAPI + React)
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8000


# Singleton settings instance
_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
