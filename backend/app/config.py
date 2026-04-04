from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Etherius"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./etherius.db"
    SECRET_KEY: str = "etherius_super_secret_key_change_in_production_2024"
    AGENT_SECRET_KEY: str = "etherius_agent_secret_key_change_in_production_2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AGENT_TOKEN_EXPIRE_HOURS: int = 720
    ANTHROPIC_API_KEY: str = ""
    DEMO_ADMIN_EMAIL: str = "admin@etheriusdemo.com"
    DEMO_ADMIN_PASSWORD: str = "Admin123!"
    DEMO_COMPANY_NAME: str = "Etherius Demo"
    DEMO_SUBSCRIPTION_KEY: str = "ETH-SUB-DEMO-2026-START"
    CEO_MASTER_KEY: str = "CHANGE_THIS_CEO_MASTER_KEY_FOR_PRODUCTION"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
