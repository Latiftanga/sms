"""
Seed two demo schools for development and testing.

  1. Demo Basic School  — Basic/JHS, day school
  2. Demo Senior High School — SHS, boarding with houses

One user per role. Fully idempotent — prints only what was actually created.

Usage:
    docker compose run --rm api python scripts/seed_schools.py
"""
import asyncio
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func


def _id() -> uuid.UUID:
    return uuid.uuid4()

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Low-level helpers ─────────────────────────────────────────────────────────

async def _get_position(session, code: str):
    from app.models.staff import StaffPosition
    pos = await session.scalar(
        select(StaffPosition).where(
            StaffPosition.code == code,
            StaffPosition.school_id.is_(None),
        )
    )
    if not pos:
        raise RuntimeError(f"System position '{code}' not found — run migrations first.")
    return pos


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


async def _ensure_staff_user(session, *, school_id, first_name, last_name,
                               gender, category, designation, employment_type,
                               date_joined, email, password, position_code,
                               positions, assigner_id=None):
    from app.core.security import hash_password
    from app.models.staff import StaffMember
    from app.models.user import User, UserRole

    existing = await session.scalar(select(User).where(User.email == email))
    if existing:
        # Return the linked staff member so callers can use it (e.g. class assignment)
        staff = await session.scalar(
            select(StaffMember).where(StaffMember.id == existing.staff_member_id)
        ) if existing.staff_member_id else None
        return staff, False

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
    return staff, True


async def _ensure_year_and_terms(session, *, school_id, education_levels):
    from app.models.academic import AcademicYear, AcademicTerm

    year = await session.scalar(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id, AcademicYear.name == "2025/2026"
        )
    )
    created_year = False
    if not year:
        year = AcademicYear(
            id=_id(), school_id=school_id, name="2025/2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 8, 1), is_current=True,
        )
        session.add(year)
        await session.flush()
        created_year = True

    terms_def = [
        ("Term 1", date(2025,  9,  1), date(2025, 12, 12), False),
        ("Term 2", date(2026,  1, 12), date(2026,  4, 10), False),
        ("Term 3", date(2026,  5,  4), date(2026,  8,  1), True),
    ]
    created_terms = 0
    for tname, start, end, is_current in terms_def:
        exists = await session.scalar(
            select(AcademicTerm).where(
                AcademicTerm.academic_year_id == year.id, AcademicTerm.name == tname
            )
        )
        if not exists:
            session.add(AcademicTerm(
                id=_id(), academic_year_id=year.id, name=tname,
                start_date=start, end_date=end,
                education_levels=education_levels, is_current=is_current,
            ))
            created_terms += 1
    await session.flush()

    if created_year:
        print(f"  + Academic year 2025/2026 with {created_terms} terms")
    elif created_terms:
        print(f"  + {created_terms} new term(s) added to 2025/2026")

    return year


async def _ensure_learning_area(session, *, school_id, name, short_name):
    from app.models.academic import LearningArea
    la = await session.scalar(
        select(LearningArea).where(LearningArea.school_id == school_id, LearningArea.name == name)
    )
    if la:
        return la, False
    la = LearningArea(id=_id(), school_id=school_id, name=name, short_name=short_name, is_active=True)
    session.add(la)
    await session.flush()
    return la, True


async def _ensure_class(session, *, school_id, education_level, level,
                         year=None, learning_area_id=None, stream=None):
    from app.models.academic import Class
    cls = await session.scalar(
        select(Class).where(
            Class.school_id == school_id, Class.level == level,
            Class.year == year, Class.stream == stream,
            Class.learning_area_id == learning_area_id,
        )
    )
    if cls:
        return cls, False
    cls = Class(
        id=_id(), school_id=school_id,
        education_level=education_level, level=level,
        year=year, learning_area_id=learning_area_id, stream=stream,
        is_active=True,
    )
    session.add(cls)
    await session.flush()
    return cls, True


async def _ensure_house(session, *, school_id, name, color):
    from app.models.academic import House
    exists = await session.scalar(
        select(House).where(House.school_id == school_id, House.name == name)
    )
    if not exists:
        session.add(House(id=_id(), school_id=school_id, name=name, color=color, is_active=True))
        return True
    return False


async def _assign_class_teacher(session, *, staff_member_id, class_id, academic_year_id):
    """Assign a staff member as class teacher for a class in a given year (idempotent)."""
    from app.models.academic import ClassTeacher
    existing = await session.scalar(
        select(ClassTeacher).where(
            ClassTeacher.class_id == class_id,
            ClassTeacher.academic_year_id == academic_year_id,
        )
    )
    if existing:
        if existing.staff_member_id != staff_member_id:
            existing.staff_member_id = staff_member_id
            return True
        return False
    session.add(ClassTeacher(
        id=_id(),
        class_id=class_id,
        staff_member_id=staff_member_id,
        academic_year_id=academic_year_id,
    ))
    await session.flush()
    return True


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

    # One user per role — no duplicate teachers
    staff_defs = [
        ("Abena",  "Mensah",  "FEMALE", "NON-TEACHING", None,          "admin@demo-basic.ttek-sms.com",   "Admin1234!",   "ADMIN"),
        ("Kweku",  "Asante",  "MALE",   "TEACHING",     "HEADTEACHER", "head@demo-basic.ttek-sms.com",    "Head1234!",    "HEADTEACHER"),
        ("Ama",    "Boateng", "FEMALE", "TEACHING",     "TEACHER",     "teacher@demo-basic.ttek-sms.com", "Teacher1234!", "CLASS_TEACHER"),
        ("Yaw",    "Darko",   "MALE",   "NON-TEACHING", None,          "bursar@demo-basic.ttek-sms.com",  "Bursar1234!",  "BURSAR"),
    ]

    staff_map: dict[str, object] = {}
    for first, last, gender, cat, desig, email, pw, pos_code in staff_defs:
        staff, new = await _ensure_staff_user(
            session, school_id=school.id,
            first_name=first, last_name=last, gender=gender,
            category=cat, designation=desig, employment_type="PERMANENT",
            date_joined=joined, email=email, password=pw,
            position_code=pos_code, positions=positions,
        )
        staff_map[pos_code] = staff
        if new:
            print(f"  + {email:<42} {pw}")

    year = await _ensure_year_and_terms(session, school_id=school.id, education_levels=["BASIC"])

    # Classes
    class_defs = [
        ("KG",    1, "A"), ("KG",    2, "A"),
        ("Basic", 1, "A"), ("Basic", 2, "A"), ("Basic", 3, "A"),
        ("Basic", 4, "A"), ("Basic", 5, "A"), ("Basic", 6, "A"),
    ]
    new_classes = 0
    first_class = None
    for level, yr, stream in class_defs:
        cls, new = await _ensure_class(
            session, school_id=school.id,
            education_level="BASIC", level=level, year=yr, stream=stream,
        )
        if new:
            new_classes += 1
        if first_class is None:
            first_class = cls

    if new_classes:
        print(f"  + {new_classes} class(es) created (KG 1–2, Basic 1–6)")

    # Assign the class teacher to Basic 1A
    if first_class and staff_map.get("CLASS_TEACHER") and year:
        assigned = await _assign_class_teacher(
            session,
            staff_member_id=staff_map["CLASS_TEACHER"].id,
            class_id=first_class.id,
            academic_year_id=year.id,
        )
        if assigned:
            print(f"  + Class teacher assigned to {first_class.name}")


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

    staff_defs = [
        ("Akosua", "Amoah",    "FEMALE", "NON-TEACHING", None,             "admin@demo-shs.ttek-sms.com",       "Admin1234!",   "ADMIN"),
        ("Kwame",  "Mensah",   "MALE",   "TEACHING",     "HEADTEACHER",    "head@demo-shs.ttek-sms.com",        "Head1234!",    "HEADTEACHER"),
        ("Efua",   "Agyemang", "FEMALE", "TEACHING",     "ASSISTANT_HEAD", "asst.head@demo-shs.ttek-sms.com",   "Head1234!",    "ASSISTANT_HEAD"),
        ("Kojo",   "Boateng",  "MALE",   "NON-TEACHING", None,             "bursar@demo-shs.ttek-sms.com",      "Bursar1234!",  "BURSAR"),
        ("Yaw",    "Peprah",   "MALE",   "NON-TEACHING", None,             "housemaster@demo-shs.ttek-sms.com", "House1234!",   "SENIOR_HOUSEMASTER"),
        ("Abena",  "Owusu",    "FEMALE", "TEACHING",     "TEACHER",        "teacher@demo-shs.ttek-sms.com",     "Teacher1234!", "CLASS_TEACHER"),
    ]

    staff_map: dict[str, object] = {}
    for first, last, gender, cat, desig, email, pw, pos_code in staff_defs:
        staff, new = await _ensure_staff_user(
            session, school_id=school.id,
            first_name=first, last_name=last, gender=gender,
            category=cat, designation=desig, employment_type="PERMANENT",
            date_joined=joined, email=email, password=pw,
            position_code=pos_code, positions=positions,
        )
        staff_map[pos_code] = staff
        if new:
            print(f"  + {email:<42} {pw}")

    year = await _ensure_year_and_terms(session, school_id=school.id, education_levels=["SHS"])

    # Learning areas
    la_defs = [
        ("General Science", "SCI"), ("General Arts",   "ART"),
        ("Business",        "BUS"), ("Home Economics", "HEC"),
    ]
    las = {}
    new_las = 0
    for name, short in la_defs:
        la, new = await _ensure_learning_area(
            session, school_id=school.id, name=name, short_name=short
        )
        las[short] = la
        if new:
            new_las += 1
    if new_las:
        print(f"  + {new_las} learning area(s) created")

    # Classes
    new_classes = 0
    first_class = None
    for yr in (1, 2, 3):
        for la_short in ("SCI", "ART", "BUS"):
            cls, new = await _ensure_class(
                session, school_id=school.id,
                education_level="SHS", level="SHS",
                year=yr, learning_area_id=las[la_short].id, stream="A",
            )
            if new:
                new_classes += 1
            if first_class is None:
                first_class = cls
    if new_classes:
        print(f"  + {new_classes} class(es) created (SHS 1–3 × Science / Arts / Business)")

    # Houses
    new_houses = 0
    for name, color in [
        ("Aggrey House",    "#1565C0"),
        ("Bannerman House", "#B71C1C"),
        ("Danquah House",   "#2E7D32"),
        ("Nkrumah House",   "#F9A825"),
    ]:
        if await _ensure_house(session, school_id=school.id, name=name, color=color):
            new_houses += 1
    if new_houses:
        print(f"  + {new_houses} house(s) created")

    # Assign class teacher to SHS 1 SCI A
    if first_class and staff_map.get("CLASS_TEACHER") and year:
        assigned = await _assign_class_teacher(
            session,
            staff_member_id=staff_map["CLASS_TEACHER"].id,
            class_id=first_class.id,
            academic_year_id=year.id,
        )
        if assigned:
            print(f"  + Class teacher assigned to {first_class.name}")


# ── Post-seed helpers ─────────────────────────────────────────────────────────

async def _promote_students(session):
    """Promote students enrolled in a non-current year into the current year."""
    from app.models.academic import AcademicTerm, AcademicYear
    from app.models.student import StudentClassEnrollment, StudentTermEnrollment

    current_years = (await session.scalars(
        select(AcademicYear).where(AcademicYear.is_current.is_(True))
    )).all()

    for current_year in current_years:
        terms = (await session.scalars(
            select(AcademicTerm).where(AcademicTerm.academic_year_id == current_year.id)
        )).all()
        if not terms:
            continue

        old_enrollments = (await session.scalars(
            select(StudentClassEnrollment)
            .join(AcademicYear, StudentClassEnrollment.academic_year_id == AcademicYear.id)
            .where(
                AcademicYear.school_id == current_year.school_id,
                AcademicYear.is_current.is_(False),
                StudentClassEnrollment.status == "ACTIVE",
            )
        )).all()

        promoted = 0
        for old_enr in old_enrollments:
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
            promoted += 1

        if promoted:
            print(f"  + Promoted {promoted} student(s) to {current_year.name}")


async def _generate_calendars(session):
    """Generate school calendars for current terms that have none yet."""
    from app.models.academic import AcademicTerm, AcademicYear, SchoolCalendar
    from app.services.calendar_generator import generate_term_calendar

    current_terms = (await session.scalars(
        select(AcademicTerm)
        .join(AcademicYear, AcademicTerm.academic_year_id == AcademicYear.id)
        .where(AcademicTerm.is_current.is_(True))
    )).all()

    for term in current_terms:
        existing = await session.scalar(
            select(func.count(SchoolCalendar.id)).where(
                SchoolCalendar.academic_term_id == term.id
            )
        )
        if not existing:
            year = await session.get(AcademicYear, term.academic_year_id)
            days = await generate_term_calendar(term, str(year.school_id), session)
            print(f"  + Calendar: {term.name} ({days} school days)")


# ── Entry point ───────────────────────────────────────────────────────────────

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

 Demo Basic School             (BASIC-DEMO)
   admin        admin@demo-basic.ttek-sms.com   Admin1234!
   headteacher  head@demo-basic.ttek-sms.com    Head1234!
   class teacher teacher@demo-basic.ttek-sms.com Teacher1234!
   bursar        bursar@demo-basic.ttek-sms.com  Bursar1234!

 Demo Senior High School       (SHS-DEMO)
   admin         admin@demo-shs.ttek-sms.com    Admin1234!
   headteacher   head@demo-shs.ttek-sms.com     Head1234!
   asst. head    asst.head@demo-shs.ttek-sms.com Head1234!
   bursar         bursar@demo-shs.ttek-sms.com   Bursar1234!
   sr. housemaster housemaster@demo-shs.ttek-sms.com House1234!
   class teacher   teacher@demo-shs.ttek-sms.com   Teacher1234!

 Platform superadmin
   admin@demo.school                            Admin1234!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    asyncio.run(main())
