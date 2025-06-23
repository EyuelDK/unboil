from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unboil_fastapi_core.dependencies import Dependencies

class Core:
    
    def __init__(self, database_url: str):
        engine = create_async_engine(database_url, echo=False)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        self.dependencies = Dependencies(session_maker)