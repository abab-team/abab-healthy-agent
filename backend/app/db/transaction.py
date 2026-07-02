from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


@contextmanager
def transactional_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def transaction(db: Session) -> Iterator[Session]:
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
