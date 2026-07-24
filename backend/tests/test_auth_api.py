"""Tests for Authentication REST API endpoints.

Verifies all five authentication endpoints:
- POST /api/v1/auth/register → User registration
- POST /api/v1/auth/login    → Credential authentication & session establishment
- POST /api/v1/auth/refresh  → Refresh token rotation
- POST /api/v1/auth/logout   → Session revocation
- GET  /api/v1/auth/me       → Current user profile retrieval
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import (
    get_current_user,
    get_login_user_use_case,
    get_logout_user_use_case,
    get_refresh_token_use_case,
    get_register_user_use_case,
)
from app.application.dto.auth_dto import TokenDTO, UserDTO
from app.core.exceptions import AuthenticationError, DuplicateEntityError
from app.domain.entities.user import User


@pytest.fixture
def mock_register_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_login_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_refresh_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_logout_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_me_use_case() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_user_dto() -> UserDTO:
    now = datetime.now(UTC)
    return UserDTO(
        id="user-12345",
        email="testuser@example.com",
        is_active=True,
        roles=["User"],
        permissions=["read:profile"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_user_entity() -> User:
    now = datetime.now(UTC)
    return User(
        id="user-12345",
        email="testuser@example.com",
        is_active=True,
        roles=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_token_dto() -> TokenDTO:
    return TokenDTO(
        access_token="test_access_token_jwt",
        refresh_token="test_refresh_token_jwt",
        token_type="Bearer",
        expires_in=1800,
    )


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    def test_successful_register(
        self,
        client: TestClient,
        app: FastAPI,
        mock_register_use_case: MagicMock,
        sample_user_dto: UserDTO,
    ) -> None:
        mock_register_use_case.execute.return_value = sample_user_dto
        app.dependency_overrides[get_register_user_use_case] = lambda: (
            mock_register_use_case
        )

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "user-12345"
        assert data["email"] == "testuser@example.com"
        assert data["is_active"] is True
        assert data["roles"] == ["User"]
        assert data["permissions"] == ["read:profile"]
        mock_register_use_case.execute.assert_called_once()

    def test_duplicate_email(
        self,
        client: TestClient,
        app: FastAPI,
        mock_register_use_case: MagicMock,
    ) -> None:
        mock_register_use_case.execute.side_effect = DuplicateEntityError(
            "User", "testuser@example.com"
        )
        app.dependency_overrides[get_register_user_use_case] = lambda: (
            mock_register_use_case
        )

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-4002"
        assert "User" in data["error"]["message"]


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_successful_login(
        self,
        client: TestClient,
        app: FastAPI,
        mock_login_use_case: MagicMock,
        sample_token_dto: TokenDTO,
    ) -> None:
        mock_login_use_case.execute.return_value = sample_token_dto
        app.dependency_overrides[get_login_user_use_case] = lambda: mock_login_use_case

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "correctpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_access_token_jwt"
        assert data["refresh_token"] == "test_refresh_token_jwt"
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 1800
        mock_login_use_case.execute.assert_called_once()

    def test_invalid_credentials(
        self,
        client: TestClient,
        app: FastAPI,
        mock_login_use_case: MagicMock,
    ) -> None:
        mock_login_use_case.execute.side_effect = AuthenticationError(
            "Invalid email or password"
        )
        app.dependency_overrides[get_login_user_use_case] = lambda: mock_login_use_case

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "wrongpassword123",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"
        assert data["error"]["message"] == "Invalid email or password"


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_success(
        self,
        client: TestClient,
        app: FastAPI,
        mock_refresh_use_case: MagicMock,
        sample_token_dto: TokenDTO,
    ) -> None:
        mock_refresh_use_case.execute.return_value = sample_token_dto
        app.dependency_overrides[get_refresh_token_use_case] = lambda: (
            mock_refresh_use_case
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "valid_refresh_token_jwt",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_access_token_jwt"
        assert data["refresh_token"] == "test_refresh_token_jwt"
        mock_refresh_use_case.execute.assert_called_once()

    def test_refresh_invalid_token(
        self,
        client: TestClient,
        app: FastAPI,
        mock_refresh_use_case: MagicMock,
    ) -> None:
        mock_refresh_use_case.execute.side_effect = AuthenticationError(
            "Invalid refresh token"
        )
        app.dependency_overrides[get_refresh_token_use_case] = lambda: (
            mock_refresh_use_case
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid_refresh_token",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "NBI-1002"


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_success(
        self,
        client: TestClient,
        app: FastAPI,
        mock_logout_use_case: MagicMock,
        sample_user_entity: User,
    ) -> None:
        mock_logout_use_case.execute.return_value = None
        app.dependency_overrides[get_logout_user_use_case] = lambda: (
            mock_logout_use_case
        )
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity

        response = client.post(
            "/api/v1/auth/logout",
            json={
                "refresh_token": "valid_refresh_token_jwt",
            },
            headers={"Authorization": "Bearer valid_access_token_jwt"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
        mock_logout_use_case.execute.assert_called_once_with("valid_refresh_token_jwt")

    def test_logout_anonymous_blocked(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(
            "/api/v1/auth/logout",
            json={
                "refresh_token": "valid_refresh_token_jwt",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"


class TestCurrentUserEndpoint:
    """Tests for GET /api/v1/auth/me."""

    def test_current_user_success(
        self,
        client: TestClient,
        app: FastAPI,
        sample_user_entity: User,
    ) -> None:
        app.dependency_overrides[get_current_user] = lambda: sample_user_entity

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid_access_token_jwt"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user-12345"
        assert data["email"] == "testuser@example.com"
        assert data["is_active"] is True

    def test_current_user_missing_header(
        self,
        client: TestClient,
    ) -> None:
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "NBI-1002"
