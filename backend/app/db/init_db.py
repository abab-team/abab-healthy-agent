from sqlalchemy.engine import Engine

from app.db.session import engine as default_engine


def init_db(engine: Engine = default_engine) -> None:
    """Database initialization placeholder for later phases."""

    return None
