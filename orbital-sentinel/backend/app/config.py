from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ORBITAL SENTINEL"
    environment: str = "development"
    api_cors_origins: str = "http://localhost:3000"

    supabase_url: str
    supabase_service_role_key: str

    celestrak_urls: str
    celestrak_timeout_seconds: int = 30

    default_window_hours: float = 3.0
    default_coarse_step_seconds: int = 60
    default_refine_step_seconds: int = 1
    coarse_broadphase_distance_km: float = 1000.0
    high_risk_distance_km: float = 1.0
    medium_risk_distance_km: float = 5.0

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"
    llm_max_output_tokens: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def celestrak_source_urls(self) -> list[str]:
        return [u.strip() for u in self.celestrak_urls.split(",") if u.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
