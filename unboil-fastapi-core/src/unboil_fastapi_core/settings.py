from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    DB_SCHEME: str = "postgresql+asyncpg"
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str

    @property
    def database_url(self) -> str:
        return f"{self.DB_SCHEME}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_prefix = "CORE_"
        env_file = ".env"
        extra = "allow"
