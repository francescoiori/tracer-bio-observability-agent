# database.py (DB setup and session management)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from tracer_bio_agent.config import Config

DATABASE_URL = Config.DATABASE_URL
engine = create_async_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Provide session to the caller
        except Exception as e:
            await session.rollback()  # Rollback if an error occurs
            raise e  # Re-raise exception for debugging
        finally:
            await session.close()  # Ensure session is closed properly

