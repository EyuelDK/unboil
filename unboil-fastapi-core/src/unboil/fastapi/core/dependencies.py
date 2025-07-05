from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .services import Services

class Dependencies:
    
    def __init__(
        self, 
        services: Services
    ):
        self.services = services
    
    async def get_db(self):
        async with self.services.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()