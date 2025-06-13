from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    stripe_webhook_secret: str
    stripe_api_key: str
        
    class Config:
        extra = "allow"
        env_file = ".env"