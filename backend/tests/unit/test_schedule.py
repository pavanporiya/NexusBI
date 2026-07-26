"""Unit tests for Schedule value object."""

import pytest

from app.domain.exceptions import DomainValidationError
from app.domain.value_objects.schedule import Schedule


def test_valid_cron_schedules() -> None:
    """Test valid cron expressions parsing and normalization."""
    s1 = Schedule("0 0 * * *")
    assert s1.expression == "0 0 * * *"
    assert str(s1) == "0 0 * * *"

    s2 = Schedule("*/5 1-5 1,15 JAN-MAR MON-FRI")
    assert s2.expression == "*/5 1-5 1,15 JAN-MAR MON-FRI"

    s3 = Schedule("  15  12  *  *  0  ")
    assert s3.expression == "15 12 * * 0"


def test_invalid_cron_schedules() -> None:
    """Test invalid cron expressions raising DomainValidationError."""
    with pytest.raises(DomainValidationError, match="must not be empty"):
        Schedule("")

    with pytest.raises(DomainValidationError, match="exactly 5 space-separated fields"):
        Schedule("0 0 * *")

    with pytest.raises(DomainValidationError, match="out of bounds"):
        Schedule("60 0 * * *")  # Minute 60 is invalid

    with pytest.raises(DomainValidationError, match="out of bounds"):
        Schedule("0 24 * * *")  # Hour 24 is invalid

    with pytest.raises(DomainValidationError, match="out of bounds"):
        Schedule("0 0 32 * *")  # Day 32 is invalid

    with pytest.raises(DomainValidationError, match="out of bounds"):
        Schedule("0 0 * 13 *")  # Month 13 is invalid

    with pytest.raises(DomainValidationError, match="out of bounds"):
        Schedule("0 0 * * 8")  # Day of week 8 is invalid

    with pytest.raises(DomainValidationError, match="cannot be greater than end"):
        Schedule("0 0 10-5 * *")

    with pytest.raises(DomainValidationError, match="positive integer"):
        Schedule("*/0 * * * *")


def test_schedule_equality_and_immutability() -> None:
    """Test equality, hashing, and immutability."""
    s1 = Schedule("0 0 * * *")
    s2 = Schedule("0 0 * * *")
    assert s1 == s2
    assert s1 == "0 0 * * *"
    assert hash(s1) == hash(s2)

    with pytest.raises(AttributeError):
        s1.expression = "1 1 * * *"  # type: ignore[misc]


def test_schedule_factory() -> None:
    """Test Schedule.create factory method."""
    assert Schedule.create(None) is None
    assert Schedule.create("") is None
    assert Schedule.create("   ") is None
    s = Schedule.create("0 0 * * *")
    assert isinstance(s, Schedule)
    assert Schedule.create(s) is s
