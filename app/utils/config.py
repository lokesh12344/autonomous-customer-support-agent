"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Stripe
    stripe_api_key: str = Field(default="", alias="STRIPE_API_KEY")
    
    # Slack
    slack_token: str = Field(default="", alias="SLACK_TOKEN")
    slack_signing_secret: str = Field(default="", alias="SLACK_SIGNING_SECRET")
    
    # Email
    smtp_server: str = Field(default="smtp.gmail.com", alias="SMTP_SERVER")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    sender_email: str = Field(default="", alias="SENDER_EMAIL")
    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")
    
    # LLM
    model_name: str = Field(default="llama3", alias="MODEL_NAME")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    
    # Database
    database_path: str = Field(default="data/db.sqlite", alias="DATABASE_PATH")
    
    # Vector Store
    vectorstore_path: str = Field(default="vectorstore/", alias="VECTORSTORE_PATH")
    
    # App
    app_name: str = Field(default="Autonomous Customer Support Agent", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
