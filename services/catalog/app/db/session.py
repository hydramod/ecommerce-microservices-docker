from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

class Base(DeclarativeBase): pass
engine = create_engine(settings.POSTGRES_DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
