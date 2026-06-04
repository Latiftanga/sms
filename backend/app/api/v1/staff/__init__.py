from app.api.v1.staff import access, bulk, records
from app.api.v1.staff._helpers import _current_rank, _to_response  # re-exported for profile.py
from app.api.v1.staff.core import router  # core.router owns prefix="/staff"

# bulk must come before /{staff_id} routes to prevent path shadowing
router.include_router(bulk.router)
router.include_router(records.router)
router.include_router(access.router)
