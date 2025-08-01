from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Only include the fields you actually use
    bitscrunch_api_key: str
    groq_api_key: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # This will ignore extra fields in .env

settings = Settings()