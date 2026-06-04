from app.api.v1.students.core import router  # owns prefix="/students"
from app.api.v1.students import bulk, enrollment, guardians

# bulk must come before /{student_id} routes to prevent path shadowing
router.include_router(bulk.router)
router.include_router(enrollment.router)
router.include_router(guardians.router)
