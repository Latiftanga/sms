"""
SchoolCalendar auto-generation service.
Called when an AcademicTerm is created.

Algorithm:
  For each date in [term.start_date, term.end_date]:
    1. If weekday not in school_schedule.school_days → WEEKEND
    2. If date in computed_holidays(year) → HOLIDAY (labelled)
    3. Else → SCHOOL_DAY

Easter and Farmers Day are computed dynamically per year.
Fixed-date holidays are loaded from GhanaPublicHoliday table.
"""
import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import AcademicTerm, SchoolCalendar
from app.models.reference import GhanaPublicHoliday
from app.models.school import SchoolSchedule

logger = logging.getLogger(__name__)


async def generate_term_calendar(
    term: AcademicTerm,
    school_id: str,
    session: AsyncSession,
    created_by_id: str | None = None,
) -> int:
    """
    Generate SchoolCalendar rows for the entire term date range.
    Returns the count of SCHOOL_DAY rows created.
    Idempotent: deletes any existing auto-generated rows before re-generating.
    """
    # Remove old auto-generated rows (re-run safe)
    from sqlalchemy import delete as sa_delete
    await session.execute(
        sa_delete(SchoolCalendar).where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.academic_term_id == term.id,
            SchoolCalendar.is_auto_generated.is_(True),
        )
    )

    schedule = await _get_schedule(school_id, session)
    school_days_set = set(schedule.school_days if schedule else [1, 2, 3, 4, 5])

    holiday_map = await _build_holiday_map(term.start_date.year, term.end_date.year, session)

    rows: list[SchoolCalendar] = []
    current = term.start_date
    school_day_count = 0

    while current <= term.end_date:
        iso_weekday = current.isoweekday()  # 1=Mon … 7=Sun

        if iso_weekday not in school_days_set:
            day_type = "WEEKEND"
            label = None
        elif current in holiday_map:
            day_type = "HOLIDAY"
            label = holiday_map[current]
        else:
            day_type = "SCHOOL_DAY"
            label = None
            school_day_count += 1

        rows.append(
            SchoolCalendar(
                school_id=school_id,
                academic_term_id=term.id,
                date=current,
                day_type=day_type,
                label=label,
                is_auto_generated=True,
                created_by=created_by_id,
            )
        )
        current += timedelta(days=1)

    session.add_all(rows)
    logger.info(
        "Generated %d calendar rows (%d school days) for term %s",
        len(rows),
        school_day_count,
        term.id,
    )
    return school_day_count


async def count_school_days(term_id: str, school_id: str, session: AsyncSession) -> int:
    """Count of SCHOOL_DAY rows — used for attendance % and WAEC totals."""
    result = await session.scalar(
        select(func.count(SchoolCalendar.id)).where(
            SchoolCalendar.academic_term_id == term_id,
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.day_type == "SCHOOL_DAY",
        )
    )
    return result or 0


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _get_schedule(school_id: str, session: AsyncSession) -> SchoolSchedule | None:
    return await session.scalar(
        select(SchoolSchedule).where(SchoolSchedule.school_id == school_id)
    )


async def _build_holiday_map(
    year_start: int, year_end: int, session: AsyncSession
) -> dict[date, str]:
    """Return {date: holiday_name} for all years in the range."""
    rows = await session.execute(
        select(GhanaPublicHoliday).where(GhanaPublicHoliday.is_active.is_(True))
    )
    holidays: dict[date, str] = {}

    for year in range(year_start, year_end + 1):
        for holiday in rows.scalars().all() if year == year_start else []:
            pass  # pre-fetch once
        rows_list = rows.scalars().all() if year == year_start else []

    # Simpler: load once then iterate
    rows2 = (await session.execute(
        select(GhanaPublicHoliday).where(GhanaPublicHoliday.is_active.is_(True))
    )).scalars().all()

    for year in range(year_start, year_end + 1):
        easter_sunday = _compute_easter(year)
        farmers_day = _compute_farmers_day(year)

        for h in rows2:
            if h.holiday_type == "FIXED" and h.month and h.day:
                try:
                    holidays[date(year, h.month, h.day)] = h.name
                except ValueError:
                    pass
            elif h.holiday_type == "EASTER_GOOD_FRIDAY":
                holidays[easter_sunday - timedelta(days=2)] = h.name
            elif h.holiday_type == "EASTER_MONDAY":
                holidays[easter_sunday + timedelta(days=1)] = h.name
            elif h.holiday_type == "FARMERS_DAY":
                holidays[farmers_day] = h.name

    return holidays


def _compute_easter(year: int) -> date:
    """Anonymous Gregorian algorithm for Easter Sunday."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _compute_farmers_day(year: int) -> date:
    """First Friday of December."""
    d = date(year, 12, 1)
    # isoweekday(): 1=Mon, 5=Fri
    days_until_friday = (4 - d.isoweekday()) % 7
    return d + timedelta(days=days_until_friday)
