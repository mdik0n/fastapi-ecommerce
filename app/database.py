from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///ecommerce.db"

engine = create_engine(DATABASE_URL, echo=True, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_timeout=30)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# --------------- Асинхронное подключение к PostgreSQL -------------------------
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from decouple import config

DATABASE_URL = config("DATABASE_URL")

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
