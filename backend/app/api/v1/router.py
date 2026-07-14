from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.knowledge_bases import router as knowledge_bases_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.speech import router as speech_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(interviews_router)
api_v1_router.include_router(knowledge_bases_router)
api_v1_router.include_router(resumes_router)
api_v1_router.include_router(speech_router)
