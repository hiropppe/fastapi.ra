import os
from collections.abc import Generator

from sqlalchemy import Engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

env = os.environ

## PostgreSQL
# DB_URL = env.get("DB_URL", "postgresql+psycopg2://tuto:tuto@localhost:5432/tuto")
# ASYNC_DB_URL = env.get("ASYNC_DB_URL", "postgresql+asyncpg://tuto:tuto@localhost:5432/tuto")

## MySQL
DB_URL = env.get("DB_URL", "mysql+pymysql://tuto:tuto@192.168.88.214:3336/tuto?charset=utf8mb4")
ASYNC_DB_URL = env.get("ASYNC_DB_URL", "mysql+aiomysql://tuto:tuto@192.168.88.214:3336/tuto?charset=utf8mb4")

connect_args = {}

# Sync Engine and Session
engine: Engine = create_engine(
    DB_URL,
    isolation_level="READ COMMITTED",
    echo=True,
    pool_size=10,
    max_overflow=40,
    connect_args=connect_args,
)


# Async Engine and Session
async_engine: AsyncEngine = create_async_engine(
    ASYNC_DB_URL,
    isolation_level="READ COMMITTED",
    echo=True,
    pool_size=10,
    max_overflow=40,
    connect_args=connect_args,
)
async_session: AsyncSession = async_sessionmaker(async_engine, class_=AsyncSession)


# Sync Session Dependency for FastAPI
def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


# Async Session Dependency for FastAPI
async def get_async_session() -> Generator[AsyncSession]:
    async with async_session() as session:
        yield session
