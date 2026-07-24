"""Tests for the Session domain entity.

Covers construction, revoke() lifecycle, is_expired / is_active predicates,
backward-compatible is_valid alias, and repr.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.entities.session import Session

# ── Fixtures ──────────────────────────────────────────────────────────


def _session(
    id: str = "s1",
    user_id: str = "u1",
    token_id: str = "tid_1",
    refresh_token: str = "rt_abc",
    expires_at: datetime | None = None,
    is_revoked: bool = False,
    revoked_at: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> Session:
    session = Session(
        id=id,
        user_id=user_id,
        token_id=token_id,
        refresh_token=refresh_token,
        expires_at=(
            expires_at
            if expires_at is not None
            else datetime.now(UTC) + timedelta(hours=1)
        ),
        is_revoked=is_revoked,
        revoked_at=revoked_at,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    if created_at is not None:
        session.created_at = created_at
    if updated_at is not None:
        session.updated_at = updated_at
    return session


# ── Construction ──────────────────────────────────────────────────────


class TestSessionConstruction:
    """Tests for Session instantiation and field defaults."""

    def test_basic_construction(self) -> None:
        session = _session()
        assert session.id == "s1"
        assert session.user_id == "u1"
        assert session.token_id == "tid_1"
        assert session.refresh_token == "rt_abc"
        assert session.is_revoked is False
        assert session.revoked_at is None
        assert session.client_ip is None
        assert session.user_agent is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_construction_with_optional_fields(self) -> None:
        session = _session(client_ip="127.0.0.1", user_agent="TestBrowser/1.0")
        assert session.client_ip == "127.0.0.1"
        assert session.user_agent == "TestBrowser/1.0"


# ── Revoke Lifecycle ─────────────────────────────────────────────────


class TestSessionRevoke:
    """Tests for the revoke() method."""

    def test_revoke_sets_is_revoked(self) -> None:
        session = _session()
        session.revoke()
        assert session.is_revoked is True

    def test_revoke_sets_revoked_at_timestamp(self) -> None:
        session = _session()
        session.revoke()
        assert session.revoked_at is not None
        assert isinstance(session.revoked_at, datetime)

    def test_revoke_updates_updated_at(self) -> None:
        past = datetime.now(UTC) - timedelta(days=1)
        session = _session(updated_at=past)
        session.revoke()
        assert session.updated_at > past

    def test_revoke_is_idempotent(self) -> None:
        session = _session()
        session.revoke()
        first_revoked_at = session.revoked_at
        first_updated_at = session.updated_at
        # Second revoke should be no-op
        session.revoke()
        assert session.revoked_at == first_revoked_at
        assert session.updated_at == first_updated_at


# ── Expiry Predicate ─────────────────────────────────────────────────


class TestSessionIsExpired:
    """Tests for the is_expired property."""

    def test_not_expired_when_future(self) -> None:
        session = _session(expires_at=datetime.now(UTC) + timedelta(hours=1))
        assert session.is_expired is False

    def test_expired_when_past(self) -> None:
        session = _session(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        assert session.is_expired is True


# ── Active Predicate ─────────────────────────────────────────────────


class TestSessionIsActive:
    """Tests for the is_active property."""

    def test_active_when_not_revoked_and_not_expired(self) -> None:
        session = _session()
        assert session.is_active is True

    def test_not_active_when_revoked(self) -> None:
        session = _session()
        session.revoke()
        assert session.is_active is False

    def test_not_active_when_expired(self) -> None:
        session = _session(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        assert session.is_active is False

    def test_not_active_when_both_revoked_and_expired(self) -> None:
        session = _session(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        session.revoke()
        assert session.is_active is False


class TestSessionIsValidBackwardCompat:
    """Tests for the is_valid backward-compatible alias."""

    def test_is_valid_matches_is_active(self) -> None:
        session = _session()
        assert session.is_valid == session.is_active

    def test_is_valid_false_when_revoked(self) -> None:
        session = _session()
        session.revoke()
        assert session.is_valid is False


class TestSessionRepr:
    """Tests for string representation."""

    def test_repr_contains_key_info(self) -> None:
        session = _session()
        r = repr(session)
        assert "Session" in r
        assert "s1" in r
