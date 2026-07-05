from fastapi import APIRouter

from app.modules.agent.api import router as agent_router
from app.modules.alerts.api import router as alerts_router
from app.modules.document_center.api import router as document_center_router
from app.modules.document_processing.api import router as document_processing_router
from app.modules.family.api import router as family_router
from app.modules.health_data.api import router as health_data_router
from app.modules.health_profile.api import router as health_profile_router
from app.modules.health_record.api import router as health_record_router
from app.modules.identity.api import router as identity_router
from app.modules.medical_timeline.api import router as medical_timeline_router
from app.modules.permissions.api import router as permissions_router
from app.modules.reports.api import router as reports_router


api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(identity_router)
api_v1_router.include_router(family_router)
api_v1_router.include_router(permissions_router)
api_v1_router.include_router(health_profile_router)
api_v1_router.include_router(health_data_router)
api_v1_router.include_router(health_record_router)
api_v1_router.include_router(medical_timeline_router)
api_v1_router.include_router(document_center_router)
api_v1_router.include_router(document_processing_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(agent_router)
