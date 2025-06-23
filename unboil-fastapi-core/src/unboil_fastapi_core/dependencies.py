from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

class Dependencies:
    
    def __init__(
        self, 
        session_maker: async_sessionmaker[AsyncSession]
    ):
        self.session_maker = session_maker
    
    async def get_db(self):
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()