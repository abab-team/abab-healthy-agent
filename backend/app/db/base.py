from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for future ORM models."""

    pass


from app.modules.identity import models as identity_models  # noqa: E402,F401
from app.modules.family import models as family_models  # noqa: E402,F401
from app.modules.permissions import models as permission_models  # noqa: E402,F401
