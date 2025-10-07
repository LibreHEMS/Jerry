"""
Unit tests for authentication module.
"""

from datetime import datetime

import jwt
import pytest

from src.utils.auth import TokenManager
from src.utils.auth import UserSession


class TestUserSession:
    """Test UserSession model."""

    def test_user_session_creation(self):
        """Test creating a user session."""
        session = UserSession(
            user_id="test-user",
            email="test@example.com",
            authenticated_at=datetime.utcnow(),
        )

        assert session.user_id == "test-user"
        assert session.email == "test@example.com"
        assert isinstance(session.authenticated_at, datetime)
        assert session.permissions == {}
        assert session.metadata == {}

    def test_user_session_with_permissions(self):
        """Test user session with permissions."""
        permissions = {"chat": True, "admin": False}
        session = UserSession(
            user_id="test-user",
            email="test@example.com",
            authenticated_at=datetime.utcnow(),
            permissions=permissions,
        )

        assert session.permissions == permissions


class TestTokenManager:
    """Test JWT token management."""

    def test_create_and_verify_token(self):
        """Test creating and verifying JWT tokens."""
        # Create token manager
        manager = TokenManager()

        # Create user session
        session = UserSession(
            user_id="test-user",
            email="test@example.com",
            authenticated_at=datetime.utcnow(),
            permissions={"chat": True},
        )

        # Create token
        token = manager.create_token(session)
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        verified_session = manager.verify_token(token)
        assert verified_session.user_id == session.user_id
        assert verified_session.email == session.email
        assert verified_session.permissions == session.permissions

    def test_token_expiry(self):
        """Test token expiration."""

        # Create token manager with short expiry
        class MockConfig:
            class Auth:
                secret_key = "test-secret"
                algorithm = "HS256"
                token_expiry_hours = -1  # Already expired

            auth = Auth()

        config = MockConfig()
        manager = TokenManager(config)

        # Create user session
        session = UserSession(
            user_id="test-user",
            email="test@example.com",
            authenticated_at=datetime.utcnow(),
        )

        # Create token
        token = manager.create_token(session)

        # Verify token should fail immediately since expiry is negative
        with pytest.raises((ValueError, jwt.ExpiredSignatureError)):
            manager.verify_token(token)

    def test_invalid_token(self):
        """Test handling of invalid tokens."""
        manager = TokenManager()

        # Test invalid token
        with pytest.raises(ValueError, match="Invalid token"):
            manager.verify_token("invalid.token.here")

        # Test empty token
        with pytest.raises(ValueError):
            manager.verify_token("")
