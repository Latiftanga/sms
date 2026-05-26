"""
SchoolCalendar generation tests.
Validates that the generator correctly classifies SCHOOL_DAY / HOLIDAY / WEEKEND.
"""
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.services.calendar_generator import _compute_easter, _compute_farmers_day


def test_easter_2025() -> None:
    easter = _compute_easter(2025)
    assert easter == date(2025, 4, 20), f"Expected 2025-04-20, got {easter}"


def test_easter_2026() -> None:
    easter = _compute_easter(2026)
    assert easter == date(2026, 4, 5), f"Expected 2026-04-05, got {easter}"


def test_farmers_day_2025() -> None:
    fd = _compute_farmers_day(2025)
    # First Friday of December 2025 = Dec 5
    assert fd == date(2025, 12, 5), f"Expected 2025-12-05, got {fd}"
    assert fd.isoweekday() == 5, "Farmers Day must be a Friday"


def test_farmers_day_2026() -> None:
    fd = _compute_farmers_day(2026)
    # First Friday of December 2026 = Dec 4
    assert fd == date(2026, 12, 4), f"Expected 2026-12-04, got {fd}"
    assert fd.isoweekday() == 5, "Farmers Day must be a Friday"


def test_farmers_day_is_always_friday() -> None:
    for year in range(2024, 2035):
        fd = _compute_farmers_day(year)
        assert fd.isoweekday() == 5, f"Farmers Day {year} is not a Friday: {fd}"
        assert fd.month == 12
        assert fd.day <= 7, f"Farmers Day {year} is not in the first week: {fd}"
