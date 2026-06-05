from fastapi import APIRouter

from app.api.v1 import attendance, auth, dashboard, health, profile, public, settings, staff, students

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(public.router)   # no auth — must be before auth middleware
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(settings.router)
api_router.include_router(staff.router)
api_router.include_router(dashboard.router)
api_router.include_router(students.router)
api_router.include_router(attendance.router)
