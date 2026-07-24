"""Unit tests for BcryptPasswordHasher.

Tests the infrastructure adapter for IPasswordHasher covering:
- Successful hashing of valid passwords
- Bcrypt hash format verification
- Successful password verification
- Failed verification with wrong password
- Password Value Object validation enforcement
- Hash uniqueness (salt variation)
- Configurable bcrypt rounds
"""

from __future__ import annotations

import pytest

from app.domain.exceptions import WeakPasswordError
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_PASSWORD = "StrongP@ss1"
WRONG_PASSWORD = "WrongP@ss2"


@pytest.fixture
def hasher() -> BcryptPasswordHasher:
    """Provide a BcryptPasswordHasher with low rounds for fast tests."""
    return BcryptPasswordHasher(rounds=4)


# ---------------------------------------------------------------------------
# Hash Generation
# ---------------------------------------------------------------------------


class TestHashPassword:
    """Tests for BcryptPasswordHasher.hash_password."""

    def test_returns_bcrypt_hash_string(self, hasher: BcryptPasswordHasher) -> None:
        """Hashing a valid password returns a non-empty bcrypt string."""
        result = hasher.hash_password(VALID_PASSWORD)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_starts_with_bcrypt_prefix(self, hasher: BcryptPasswordHasher) -> None:
        """Bcrypt hashes start with $2b$ (or $2a$/$2y$) identifier."""
        result = hasher.hash_password(VALID_PASSWORD)
        assert result.startswith(("$2b$", "$2a$", "$2y$"))

    def test_hash_differs_from_plaintext(self, hasher: BcryptPasswordHasher) -> None:
        """The hash must never equal the original plaintext password."""
        result = hasher.hash_password(VALID_PASSWORD)
        assert result != VALID_PASSWORD

    def test_same_password_produces_different_hashes(
        self, hasher: BcryptPasswordHasher
    ) -> None:
        """Each hash uses a unique salt, so identical passwords differ."""
        hash1 = hasher.hash_password(VALID_PASSWORD)
        hash2 = hasher.hash_password(VALID_PASSWORD)
        assert hash1 != hash2

    def test_rejects_weak_password_too_short(
        self, hasher: BcryptPasswordHasher
    ) -> None:
        """Passwords below minimum length are rejected."""
        with pytest.raises(WeakPasswordError, match="at least 8 characters"):
            hasher.hash_password("Sh@1")

    def test_rejects_weak_password_no_uppercase(
        self, hasher: BcryptPasswordHasher
    ) -> None:
        """Passwords without uppercase are rejected."""
        with pytest.raises(WeakPasswordError, match="uppercase"):
            hasher.hash_password("weakpass@1")

    def test_rejects_weak_password_no_lowercase(
        self, hasher: BcryptPasswordHasher
    ) -> None:
        """Passwords without lowercase are rejected."""
        with pytest.raises(WeakPasswordError, match="lowercase"):
            hasher.hash_password("WEAKPASS@1")

    def test_rejects_weak_password_no_digit(self, hasher: BcryptPasswordHasher) -> None:
        """Passwords without digits are rejected."""
        with pytest.raises(WeakPasswordError, match="digit"):
            hasher.hash_password("WeakPass@a")

    def test_rejects_weak_password_no_special(
        self, hasher: BcryptPasswordHasher
    ) -> None:
        """Passwords without special characters are rejected."""
        with pytest.raises(WeakPasswordError, match="special"):
            hasher.hash_password("WeakPass1a")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


class TestVerifyPassword:
    """Tests for BcryptPasswordHasher.verify_password."""

    def test_correct_password_returns_true(self, hasher: BcryptPasswordHasher) -> None:
        """Verification succeeds for the correct plaintext password."""
        hashed = hasher.hash_password(VALID_PASSWORD)
        assert hasher.verify_password(VALID_PASSWORD, hashed) is True

    def test_wrong_password_returns_false(self, hasher: BcryptPasswordHasher) -> None:
        """Verification fails for an incorrect plaintext password."""
        hashed = hasher.hash_password(VALID_PASSWORD)
        assert hasher.verify_password(WRONG_PASSWORD, hashed) is False

    def test_empty_password_returns_false(self, hasher: BcryptPasswordHasher) -> None:
        """Verification fails gracefully for empty password input."""
        hashed = hasher.hash_password(VALID_PASSWORD)
        assert hasher.verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestConfiguration:
    """Tests for BcryptPasswordHasher configuration."""

    def test_custom_rounds(self) -> None:
        """Hasher can be instantiated with custom bcrypt rounds."""
        hasher = BcryptPasswordHasher(rounds=10)
        hashed = hasher.hash_password(VALID_PASSWORD)
        assert hasher.verify_password(VALID_PASSWORD, hashed) is True

    def test_default_rounds(self) -> None:
        """Default hasher uses 12 rounds and produces valid hashes."""
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash_password(VALID_PASSWORD)
        assert hasher.verify_password(VALID_PASSWORD, hashed) is True
