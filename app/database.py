from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///ecommerce_db"

engine = create_engine(DATABASE_URL, echo=True, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_timeout=30)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
