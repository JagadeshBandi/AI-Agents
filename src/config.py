import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None
    
    # Model Configuration
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Training Configuration
    training_data_path: str = "./data/training/"
    model_output_path: str = "./models/"
    use_gpu: bool = True
    
    # Web Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
