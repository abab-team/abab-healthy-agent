from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for future ORM models."""

    pass


from app.modules.identity import models as identity_models  # noqa: E402,F401
from app.modules.family import models as family_models  # noqa: E402,F401
from app.modules.permissions import models as permission_models  # noqa: E402,F401
from app.modules.health_profile import models as health_profile_models  # noqa: E402,F401
from app.modules.health_data import models as health_data_models  # noqa: E402,F401
from app.modules.health_record import models as health_record_models  # noqa: E402,F401
from app.modules.medical_timeline import models as medical_timeline_models  # noqa: E402,F401
from app.modules.document_center import models as document_center_models  # noqa: E402,F401
from app.modules.document_processing import models as document_processing_models  # noqa: E402,F401
from app.modules.reports import models as report_models  # noqa: E402,F401
from app.modules.alerts import models as alert_models  # noqa: E402,F401
from app.agent import models as agent_models  # noqa: E402,F401
from app.modules.audit import models as audit_models  # noqa: E402,F401
