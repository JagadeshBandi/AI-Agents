import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tapapply.db")
    redis_url: str = "redis://localhost:6379"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    max_file_size: int = 10 * 1024 * 1024
    allowed_resume_formats: list = [".pdf", ".docx", ".doc", ".txt"]

    autopilot_cycle_seconds: int = 8
    transient_file_ttl_seconds: int = 300  # wipe temp files after 5 minutes

    proxy_list: list = []  # Comma-separated residential proxy URLs

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
