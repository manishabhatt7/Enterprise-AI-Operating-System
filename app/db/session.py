# Database session helpers
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.database import engine

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)