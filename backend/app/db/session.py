from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///:memory:"

settings = get_settings()
database_url = settings.DATABASE_URL or DEFAULT_DATABASE_URL

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
