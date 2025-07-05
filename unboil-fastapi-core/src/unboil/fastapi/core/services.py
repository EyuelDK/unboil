from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .config import Config

class Services:
    
    def __init__(self, config: Config):
        self.engine = create_async_engine(config.database_url, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)