"""Tests for domain Value Objects and Domain Exceptions.

Covers Email, Password, immutability, normalization, validation rules,
equality support, masking, and exception inheritance hierarchy.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.domain.exceptions import (
    DomainValidationError,
    InvalidEmailError,
    InvalidRoleError,
    UserValidationError,
    WeakPasswordError,
)
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password

# ── Email Value Object Tests ──────────────────────────────────────────


class TestEmailValueObject:
    """Tests for Email Value Object behavior and invariants."""

    def test_email_creation_and_normalization(self) -> None:
        email = Email("  User@Example.COM  ")
        assert email.value == "user@example.com"
        assert str(email) == "user@example.com"

    def test_email_from_email_object(self) -> None:
        orig = Email("test@example.com")
        copy = Email(orig)
        assert copy.value == "test@example.com"
        assert copy == orig

    def test_email_immutability(self) -> None:
        email = Email("test@example.com")
        with pytest.raises(FrozenInstanceError):
            email.value = "other@example.com"  # type: ignore[misc]

    def test_empty_email_raises_invalid_email_error(self) -> None:
        with pytest.raises(InvalidEmailError, match="email must not be empty"):
            Email("")

    def test_whitespace_email_raises_invalid_email_error(self) -> None:
        with pytest.raises(InvalidEmailError, match="email must not be empty"):
            Email("   ")

    def test_invalid_format_raises_invalid_email_error(self) -> None:
        with pytest.raises(InvalidEmailError, match="Invalid email address format"):
            Email("not-an-email")

    def test_non_string_raises_invalid_email_error(self) -> None:
        with pytest.raises(InvalidEmailError, match="must be a string"):
            Email(123)  # type: ignore[arg-type]

    def test_email_equality(self) -> None:
        e1 = Email("test@example.com")
        e2 = Email("TEST@EXAMPLE.COM")
        assert e1 == e2
        assert e1 == "test@example.com"
        assert e1 == "TEST@EXAMPLE.COM"
        assert e1 != "other@example.com"
        assert e1 != 123

    def test_email_hashable(self) -> None:
        e1 = Email("test@example.com")
        e2 = Email("TEST@EXAMPLE.COM")
        s = {e1, e2}
        assert len(s) == 1
        assert e1 in s

    def test_email_repr(self) -> None:
        email = Email("test@example.com")
        assert repr(email) == "Email('test@example.com')"


# ── Password Value Object Tests ───────────────────────────────────────


class TestPasswordValueObject:
    """Tests for Password Value Object behavior and complexity rules."""

    def test_valid_password(self) -> None:
        pwd = Password("StrongP@ss1")
        assert pwd.value == "StrongP@ss1"

    def test_password_immutability(self) -> None:
        pwd = Password("StrongP@ss1")
        with pytest.raises(FrozenInstanceError):
            pwd.value = "NewP@ssword1"  # type: ignore[misc]

    def test_password_non_string_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="must be a string"):
            Password(12345678)  # type: ignore[arg-type]

    def test_too_short_password_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="at least 8 characters"):
            Password("Short1!")

    def test_missing_uppercase_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="uppercase"):
            Password("weakp@ss1")

    def test_missing_lowercase_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="lowercase"):
            Password("WEAKP@SS1")

    def test_missing_digit_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="digit"):
            Password("WeakP@ssword")

    def test_missing_special_char_raises_weak_password_error(self) -> None:
        with pytest.raises(WeakPasswordError, match="special character"):
            Password("WeakPassword1")

    def test_password_masking(self) -> None:
        pwd = Password("StrongP@ss1")
        assert str(pwd) == "********"
        assert repr(pwd) == "Password(********)"
        # Confirm underlying value is preserved for application layer hashing
        assert pwd.value == "StrongP@ss1"


# ── Domain Exceptions Hierarchy Tests ─────────────────────────────────


class TestDomainExceptionsHierarchy:
    """Tests exception inheritance relationships."""

    def test_exceptions_inherit_from_domain_validation_error_and_value_error(
        self,
    ) -> None:
        err1 = InvalidEmailError("bad email")
        err2 = WeakPasswordError("weak password")
        err3 = InvalidRoleError("invalid role")
        err4 = UserValidationError("invalid user state")

        for err in (err1, err2, err3, err4):
            assert isinstance(err, DomainValidationError)
            assert isinstance(err, ValueError)
            assert isinstance(err, Exception)
