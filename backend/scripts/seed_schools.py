"""
Seed two demo schools for development and testing.

  1. Demo Basic School  — Basic/JHS, day school
  2. Demo Senior High School — SHS, boarding with houses

Usage:
    docker compose run --rm api python scripts/seed_schools.py

Idempotent — safe to run multiple times (skips existing records).
"""
import asyncio
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select


def _id() -> uuid.UUID:
    return uuid.uuid4()

def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _get_position(session, code: str):
    from app.models.staff import StaffPosition
    pos = await session.scalar(
        select(StaffPosition).where(
            StaffPosition.code == code,
            StaffPosition.school_id.is_(None),
        )
    )
    if not pos:
        raise RuntimeError(f"System position '{code}' not found — have you run migrations?")
    return pos


async def _ensure_staff_user(
    session, *,
    school_id: uuid.UUID,
    first_name: str, last_name: str, gender: str,
    category: str, designation: str | None, employment_type: str,
    date_joined: date,
    email: str, password: str,
    position_code: str, positions: dict,
    assigner_id: uuid.UUID | None = None,
):
    from app.core.security import hash_password
    from app.models.staff import StaffMember
    from app.models.user import User, UserRole

    if await session.scalar(select(User).where(User.email == email)):
        return False

    staff = StaffMember(
        id=_id(), school_id=school_id,
        first_name=first_name, last_name=last_name,
        gender=gender, category=category,
        designation=designation, employment_type=employment_type,
        date_joined=date_joined, is_active=True,
    )
    session.add(staff)
    await session.flush()

    user = User(
        id=_id(), email=email,
        password_hash=hash_password(password),
        system_role="SCHOOL_STAFF",
        school_id=school_id,
        staff_member_id=staff.id,
        is_active=True, is_verified=True,
    )
    session.add(user)
    await session.flush()

    session.add(UserRole(
        id=_id(), user_id=user.id,
        role_id=positions[position_code].id,
        assigned_by=assigner_id,
        assigned_at=_now(),
    ))
    await session.flush()
    return True


async def _ensure_school(session, *, code, name, slug, education_levels,
                          facility_type, has_houses, accent_color, motto=None):
    from app.models.school import School, SchoolConfig, SchoolSchedule

    school = await session.scalar(select(School).where(School.code == code))
    if school:
        return school, False

    school = School(
        id=_id(), name=name, code=code, slug=slug,
        country="Ghana", education_levels=education_levels,
        facility_type=facility_type, has_houses=has_houses,
        has_fees_module=True, accent_color=accent_color,
        motto=motto, is_active=True,
    )
    session.add(school)
    await session.flush()
    session.add(SchoolConfig(id=_id(), school_id=school.id))
    session.add(SchoolSchedule(id=_id(), school_id=school.id, school_days=[1, 2, 3, 4, 5]))
    await session.flush()
    return school, True


async def _ensure_year_and_terms(session, *, school_id, education_levels):
    from app.models.academic import AcademicYear, AcademicTerm

    year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id, AcademicYear.name == "2025/2026"
        )
    )
    if not year:
        year = AcademicYear(
            id=_id(), school_id=school_id, name="2025/2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 8, 1), is_current=True,
        )
        session.add(year)
        await session.flush()

    terms = [
        ("Term 1", date(2025,  9,  1), date(2025, 12, 12), False),
        ("Term 2", date(2026,  1, 12), date(2026,  4, 10), False),
        ("Term 3", date(2026,  5,  4), date(2026,  8,  1), True),   # today is in Term 3
    ]
    for name, start, end, is_current in terms:
        exists = await session.scalar(
            select(AcademicTerm).where(
                AcademicTerm.academic_year_id == year.id, AcademicTerm.name == name
            )
        )
        if not exists:
            session.add(AcademicTerm(
                id=_id(), academic_year_id=year.id, name=name,
                start_date=start, end_date=end,
                education_levels=education_levels, is_current=is_current,
            ))
    await session.flush()


async def _ensure_learning_area(session, *, school_id, name, short_name):
    from app.models.academic import LearningArea
    la = await session.scalar(
        select(LearningArea).where(LearningArea.school_id == school_id, LearningArea.name == name)
    )
    if la:
        return la
    la = LearningArea(id=_id(), school_id=school_id, name=name, short_name=short_name, is_active=True)
    session.add(la)
    await session.flush()
    return la


async def _ensure_class(session, *, school_id, education_level, level,
                         year=None, learning_area_id=None, stream=None):
    from app.models.academic import Class
    exists = await session.scalar(
        select(Class).where(
            Class.school_id == school_id, Class.level == level,
            Class.year == year, Class.stream == stream,
            Class.learning_area_id == learning_area_id,
        )
    )
    if not exists:
        session.add(Class(
            id=_id(), school_id=school_id,
            education_level=education_level, level=level,
            year=year, learning_area_id=learning_area_id, stream=stream,
            is_active=True,
        ))


async def _ensure_house(session, *, school_id, name, color):
    from app.models.academic import House
    exists = await session.scalar(
        select(House).where(House.school_id == school_id, House.name == name)
    )
    if not exists:
        session.add(House(id=_id(), school_id=school_id, name=name, color=color, is_active=True))


# ── Basic School ──────────────────────────────────────────────────────────────

async def seed_basic(session, positions):
    school, created = await _ensure_school(
        session,
        code="BASIC-DEMO", name="Demo Basic School", slug="demo-basic",
        education_levels=["BASIC"], facility_type="DAY",
        has_houses=False, accent_color="#1B5E20",
        motto="Knowledge is the key",
    )
    print(f"\n[Basic] {'Created' if created else 'Exists'}: {school.name}")

    joined = date(2020, 9, 1)
    staff = [
        ("Abena",  "Mensah",   "FEMALE", "NON-TEACHING", None,           "admin@demo-basic.ttek-sms.com",    "Admin1234!",   "ADMIN"),
        ("Kweku",  "Asante",   "MALE",   "TEACHING",     "HEADTEACHER",  "head@demo-basic.ttek-sms.com",     "Head1234!",    "HEADTEACHER"),
        ("Ama",    "Boateng",  "FEMALE", "TEACHING",     "TEACHER",      "teacher1@demo-basic.ttek-sms.com", "Teacher1234!", "CLASS_TEACHER"),
        ("Kofi",   "Osei",     "MALE",   "TEACHING",     "TEACHER",      "teacher2@demo-basic.ttek-sms.com", "Teacher1234!", "CLASS_TEACHER"),
        ("Akua",   "Frimpong", "FEMALE", "TEACHING",     "TEACHER",      "teacher3@demo-basic.ttek-sms.com", "Teacher1234!", "CLASS_TEACHER"),
        ("Yaw",    "Darko",    "MALE",   "NON-TEACHING", None,           "bursar@demo-basic.ttek-sms.com",   "Bursar1234!",  "BURSAR"),
    ]
    for first, last, gender, cat, desig, email, pw, pos_code in staff:
        created = await _ensure_staff_user(
            session, school_id=school.id,
            first_name=first, last_name=last, gender=gender,
            category=cat, designation=desig, employment_type="PERMANENT",
            date_joined=joined, email=email, password=pw,
            position_code=pos_code, positions=positions,
        )
        if created:
            print(f"  + {email:<40} {pw}")

    await _ensure_year_and_terms(session, school_id=school.id, education_levels=["BASIC"])

    for level, yr, stream in [
        ("KG",    1, "A"), ("KG",    2, "A"),
        ("Basic", 1, "A"), ("Basic", 2, "A"), ("Basic", 3, "A"),
        ("Basic", 4, "A"), ("Basic", 5, "A"), ("Basic", 6, "A"),
    ]:
        await _ensure_class(session, school_id=school.id,
                             education_level="BASIC", level=level, year=yr, stream=stream)
    print(f"  + 8 classes (KG 1–2, Basic 1–6)")


# ── SHS ───────────────────────────────────────────────────────────────────────

async def seed_shs(session, positions):
    school, created = await _ensure_school(
        session,
        code="SHS-DEMO", name="Demo Senior High School", slug="demo-shs",
        education_levels=["SHS"], facility_type="BOARDING",
        has_houses=True, accent_color="#B71C1C",
        motto="Ora et Labora",
    )
    print(f"\n[SHS]   {'Created' if created else 'Exists'}: {school.name}")

    joined = date(2019, 9, 1)
    staff = [
        ("Akosua", "Amoah",    "FEMALE", "NON-TEACHING", None,             "admin@demo-shs.ttek-sms.com",      "Admin1234!",   "ADMIN"),
        ("Kwame",  "Mensah",   "MALE",   "TEACHING",     "HEADTEACHER",    "head@demo-shs.ttek-sms.com",       "Head1234!",    "HEADTEACHER"),
        ("Efua",   "Agyemang", "FEMALE", "TEACHING",     "ASSISTANT_HEAD", "asst.head@demo-shs.ttek-sms.com",  "Head1234!",    "ASSISTANT_HEAD"),
        ("Kojo",   "Boateng",  "MALE",   "NON-TEACHING", None,             "bursar@demo-shs.ttek-sms.com",     "Bursar1234!",  "BURSAR"),
        ("Yaw",    "Peprah",   "MALE",   "NON-TEACHING", None,             "housemaster@demo-shs.ttek-sms.com","House1234!",   "SENIOR_HOUSEMASTER"),
        ("Abena",  "Owusu",    "FEMALE", "TEACHING",     "TEACHER",        "teacher1@demo-shs.ttek-sms.com",   "Teacher1234!", "CLASS_TEACHER"),
        ("Fiifi",  "Asante",   "MALE",   "TEACHING",     "TEACHER",        "teacher2@demo-shs.ttek-sms.com",   "Teacher1234!", "CLASS_TEACHER"),
        ("Adwoa",  "Darko",    "FEMALE", "TEACHING",     "TEACHER",        "teacher3@demo-shs.ttek-sms.com",   "Teacher1234!", "CLASS_TEACHER"),
        ("Kwesi",  "Frimpong", "MALE",   "TEACHING",     "TEACHER",        "teacher4@demo-shs.ttek-sms.com",   "Teacher1234!", "CLASS_TEACHER"),
    ]
    for first, last, gender, cat, desig, email, pw, pos_code in staff:
        created = await _ensure_staff_user(
            session, school_id=school.id,
            first_name=first, last_name=last, gender=gender,
            category=cat, designation=desig, employment_type="PERMANENT",
            date_joined=joined, email=email, password=pw,
            position_code=pos_code, positions=positions,
        )
        if created:
            print(f"  + {email:<40} {pw}")

    await _ensure_year_and_terms(session, school_id=school.id, education_levels=["SHS"])

    la_defs = [
        ("General Science", "SCI"), ("General Arts",   "ART"),
        ("Business",        "BUS"), ("Home Economics", "HEC"),
    ]
    las = {}
    for name, short in la_defs:
        las[short] = await _ensure_learning_area(
            session, school_id=school.id, name=name, short_name=short
        )
    print(f"  + {len(la_defs)} learning areas")

    for yr in (1, 2, 3):
        for la_short in ("SCI", "ART", "BUS"):
            await _ensure_class(
                session, school_id=school.id,
                education_level="SHS", level="SHS",
                year=yr, learning_area_id=las[la_short].id, stream="A",
            )
    print(f"  + 9 classes (SHS 1–3 × Science / Arts / Business)")

    for name, color in [
        ("Aggrey House",   "#1565C0"),
        ("Bannerman House","#B71C1C"),
        ("Danquah House",  "#2E7D32"),
        ("Nkrumah House",  "#F9A825"),
    ]:
        await _ensure_house(session, school_id=school.id, name=name, color=color)
    print(f"  + 4 houses")


# ── Entry point ───────────────────────────────────────────────────────────────

async def _promote_students(session):
    """Promote any students enrolled in a non-current year into the current year."""
    from app.models.academic import AcademicTerm, AcademicYear
    from app.models.student import StudentClassEnrollment, StudentTermEnrollment

    schools = (await session.scalars(
        select(AcademicYear).where(AcademicYear.is_current.is_(True))
    )).all()

    for current_year in schools:
        terms = (await session.scalars(
            select(AcademicTerm).where(AcademicTerm.academic_year_id == current_year.id)
        )).all()
        if not terms:
            continue

        # Find students still enrolled in a previous year for this school
        old_enrollments = (await session.scalars(
            select(StudentClassEnrollment)
            .join(AcademicYear, StudentClassEnrollment.academic_year_id == AcademicYear.id)
            .where(
                AcademicYear.school_id == current_year.school_id,
                AcademicYear.is_current.is_(False),
                StudentClassEnrollment.status == "ACTIVE",
            )
        )).all()

        for old_enr in old_enrollments:
            # Skip if already enrolled in current year
            exists = await session.scalar(
                select(StudentClassEnrollment).where(
                    StudentClassEnrollment.student_id == old_enr.student_id,
                    StudentClassEnrollment.academic_year_id == current_year.id,
                )
            )
            if exists:
                continue

            new_enr = StudentClassEnrollment(
                id=_id(),
                student_id=old_enr.student_id,
                class_id=old_enr.class_id,
                academic_year_id=current_year.id,
                student_type=old_enr.student_type,
                house_id=old_enr.house_id,
                register_number=old_enr.register_number,
                status="ACTIVE",
            )
            session.add(new_enr)
            await session.flush()

            for term in terms:
                session.add(StudentTermEnrollment(
                    id=_id(),
                    student_class_enrollment_id=new_enr.id,
                    academic_term_id=term.id,
                    enrolled_date=date.today(),
                    fee_status="NOT_APPLICABLE",
                ))

        if old_enrollments:
            print(f"  + Promoted {len(old_enrollments)} student enrollments to {current_year.name}")


async def _generate_calendars(session):
    """Generate school calendars for all current terms that have none yet."""
    from app.models.academic import AcademicTerm, AcademicYear, SchoolCalendar
    from app.services.calendar_generator import generate_term_calendar
    from sqlalchemy import func

    current_terms = await session.scalars(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicTerm.is_current.is_(True))
    )
    for term in current_terms:
        existing = await session.scalar(
            select(func.count(SchoolCalendar.id)).where(
                SchoolCalendar.academic_term_id == term.id
            )
        )
        if not existing:
            year = await session.get(AcademicYear, term.academic_year_id)
            days = await generate_term_calendar(term, str(year.school_id), session)
            print(f"  + Calendar generated for term {term.name} ({days} school days)")


async def main():
    from app.core.db import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        positions = {}
        for code in ("ADMIN", "HEADTEACHER", "ASSISTANT_HEAD",
                     "BURSAR", "CLASS_TEACHER", "HOUSEMASTER", "SENIOR_HOUSEMASTER"):
            positions[code] = await _get_position(session, code)

        await seed_basic(session, positions)
        await seed_shs(session, positions)
        await session.flush()
        await _promote_students(session)
        await _generate_calendars(session)
        await session.commit()

    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SEED COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Demo Basic School
   admin       admin@demo-basic.ttek-sms.com        Admin1234!
   headteacher head@demo-basic.ttek-sms.com         Head1234!
   teachers    teacher1–3@demo-basic.ttek-sms.com   Teacher1234!
   bursar      bursar@demo-basic.ttek-sms.com       Bursar1234!

 Demo Senior High School
   admin       admin@demo-shs.ttek-sms.com          Admin1234!
   headteacher head@demo-shs.ttek-sms.com           Head1234!
   asst. head  asst.head@demo-shs.ttek-sms.com      Head1234!
   bursar      bursar@demo-shs.ttek-sms.com         Bursar1234!
   housemaster housemaster@demo-shs.ttek-sms.com    House1234!
   teachers    teacher1–4@demo-shs.ttek-sms.com     Teacher1234!

 Platform superadmin
   admin@demo.school                          Admin1234!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    asyncio.run(main())
