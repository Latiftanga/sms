from app.api.v1.students.core import router  # owns prefix="/students"
from app.api.v1.students import enrollment, guardians

router.include_router(enrollment.router)
router.include_router(guardians.router)
