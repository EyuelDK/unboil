from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unboil.fastapi.core.config import Config

class Dependencies:
    
    def __init__(
        self, 
        config: Config
    ):
        engine = create_async_engine(config.database_url, echo=False)
        self.session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async def get_db(self):
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()