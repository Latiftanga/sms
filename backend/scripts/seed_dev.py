"""
Development seed — creates a demo school and a school-admin user.

Usage:
    docker compose run --rm api python scripts/seed_dev.py

Credentials created:
    Email:    admin@demo.school
    Password: Admin1234!

Safe to run multiple times (idempotent).
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select


async def main() -> None:
    from app.core.db import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.school import School, SchoolConfig, SchoolSchedule
    from app.models.staff import StaffPosition
    from app.models.user import User

    async with AsyncSessionLocal() as session:

        # ── School ────────────────────────────────────────────────────
        school = await session.scalar(select(School).where(School.code == "DEMO"))
        if not school:
            school = School(
                id=uuid.uuid4(),
                name="TTEK Demo School",
                code="DEMO",
                slug="ttek-demo",
                education_levels=["BASIC"],
                accent_color="#185FA5",
                is_active=True,
            )
            session.add(school)
            await session.flush()

            session.add(SchoolConfig(id=uuid.uuid4(), school_id=school.id))
            session.add(SchoolSchedule(
                id=uuid.uuid4(),
                school_id=school.id,
                school_days=[1, 2, 3, 4, 5],
            ))
            print(f"Created school '{school.name}' (id={school.id})")
        else:
            print(f"School already exists (id={school.id})")

        # ── Find the seeded ADMIN position (system template, school_id=NULL) ──
        admin_position = await session.scalar(
            select(StaffPosition).where(
                StaffPosition.code == "ADMIN",
                StaffPosition.school_id.is_(None),
            )
        )

        # ── School admin user ─────────────────────────────────────────
        email = "admin@demo.school"
        user = await session.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=hash_password("Admin1234!"),
                system_role="SCHOOL_STAFF",
                school_id=school.id,
                position_id=admin_position.id if admin_position else None,
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            print(f"Created school admin '{email}' with password 'Admin1234!'")
            if admin_position:
                print(f"  Assigned position: {admin_position.name} (all permissions)")
            else:
                print("  Warning: ADMIN position not found — user has no permissions")
        else:
            # Ensure existing user has the admin position
            if admin_position and user.position_id != admin_position.id:
                user.position_id = admin_position.id
                print(f"Updated '{email}' position to ADMIN")
            else:
                print(f"User '{email}' already exists")

        await session.commit()

    print("\nDev seed complete.")
    print("  Login:    admin@demo.school")
    print("  Password: Admin1234!")


if __name__ == "__main__":
    asyncio.run(main())
