"""
Centralized, environment-driven configuration.
Nothing here is hard-coded that the spec asks to be configurable
(AI provider, pricing, scoring weights, trial limits).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "placement_analyzer"

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # AI
    ai_provider: str = "mock"  # mock | openai | gemini | mistral
    openai_api_key: str = ""
    gemini_api_key: str = ""
    mistral_api_key: str = ""

    # RAG (optional, used by services/rag.py if enabled)
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    analysis_price: int = 19900  # in paise (INR) => ₹199.00
    currency: str = "INR"

    # Trial system (legacy compatibility; product is unlimited-analysis)
    free_analyses_limit: int = 0

    # Scoring weights (must sum to 1.0). Configurable per product rule #11.
    weight_technical_skills: float = 0.30
    weight_ai_ml_skills: float = 0.20
    weight_jd_alignment: float = 0.20
    weight_experience: float = 0.10
    weight_projects: float = 0.10
    weight_resume_quality: float = 0.10

    # File upload limits
    max_upload_size_mb: int = 8
    allowed_resume_extensions: str = ".pdf,.docx"

    frontend_url: str = "http://localhost:3000"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
