"""
Assign default roles to SCHOOL_STAFF accounts that have no roles assigned.

This fixes accounts created before role auto-assignment was in place, or
accounts whose staff member has no matching designation/category.

Usage:
    docker compose run --rm api python scripts/assign_missing_roles.py

    # To preview without committing:
    docker compose run --rm api python scripts/assign_missing_roles.py --dry-run

    # To assign a specific role to one user by email:
    docker compose run --rm api python scripts/assign_missing_roles.py \
        --email user@school.gh --role HEADTEACHER
"""
import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

_DESIGNATION_TO_ROLE_CODE: dict[str, str] = {
    "HEADTEACHER":        "HEADTEACHER",
    "ASSISTANT_HEAD":     "ASSISTANT_HEAD",
    "BURSAR":             "BURSAR",
    "HOUSEMASTER":        "HOUSEMASTER",
    "SENIOR_HOUSEMASTER": "SENIOR_HOUSEMASTER",
}


async def main(dry_run: bool, email: str | None, force_role: str | None) -> None:
    from app.core.db import AsyncSessionLocal
    from app.models.staff import StaffMember, StaffPosition
    from app.models.user import User, UserRole

    async with AsyncSessionLocal() as session:
        # Load all SCHOOL_STAFF users with no roles
        if email:
            users_q = select(User).where(
                User.email == email,
                User.system_role == "SCHOOL_STAFF",
            ).options(selectinload(User.staff_member))
        else:
            users_q = select(User).where(
                User.system_role == "SCHOOL_STAFF",
            ).options(selectinload(User.staff_member))

        all_users = list(await session.scalars(users_q))

        users_without_roles: list[User] = []
        for u in all_users:
            count = await session.scalar(
                select(UserRole).where(UserRole.user_id == u.id)
            )
            if not count:
                users_without_roles.append(u)

        if not users_without_roles:
            print("All accounts already have roles assigned. Nothing to do.")
            return

        print(f"Found {len(users_without_roles)} account(s) with no roles:\n")

        for user in users_without_roles:
            member: StaffMember | None = user.staff_member

            if force_role:
                role_code = force_role.upper()
            elif member:
                role_code = _DESIGNATION_TO_ROLE_CODE.get(member.designation or "")
                if not role_code and member.category == "TEACHING":
                    role_code = "CLASS_TEACHER"
            else:
                role_code = None

            name = f"{member.first_name} {member.last_name}" if member else "(no staff record)"
            print(f"  {user.email}  [{name}]  →  role: {role_code or '(none — skipping)'}")

            if not role_code:
                continue

            # Look up the system template position
            pos = await session.scalar(
                select(StaffPosition).where(
                    StaffPosition.code == role_code,
                    StaffPosition.is_system_template.is_(True),
                )
            )
            if not pos:
                print(f"    ✗  Position '{role_code}' not found in DB (is_system_template=True).")
                continue

            if dry_run:
                print(f"    (dry-run) would assign: {pos.name} (id={pos.id})")
            else:
                session.add(UserRole(
                    user_id=user.id,
                    role_id=pos.id,
                    assigned_by=None,
                    assigned_at=datetime.now(UTC),
                ))
                print(f"    ✓  Assigned: {pos.name}")

        if not dry_run:
            await session.commit()
            print("\nDone. Roles committed.")
            print("Note: permission caches will refresh automatically on next login.")
        else:
            print("\n(Dry run — no changes written)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign default roles to unroled staff accounts.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing")
    parser.add_argument("--email", default=None, help="Target a specific user by email")
    parser.add_argument("--role", default=None,
                        help="Force a specific role code (HEADTEACHER, ADMIN, BURSAR, CLASS_TEACHER, ...)")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, email=args.email, force_role=args.role))
