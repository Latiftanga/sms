from fastapi import APIRouter

from app.api.v1.settings import academic, admin, school

router = APIRouter(prefix="/settings", tags=["settings"])
router.include_router(school.router)
router.include_router(academic.router)
router.include_router(admin.router)
