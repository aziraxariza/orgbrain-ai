from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://orgbrain:orgbrain@localhost:5432/orgbrain"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    gemini_api_key: str = ""
    groq_api_key: str = ""

    synthetic_employees: int = 300
    synthetic_projects: int = 50
    synthetic_tasks: int = 500

    environment: str = "development"


settings = Settings()
