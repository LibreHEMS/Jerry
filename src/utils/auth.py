"""
Inter-service authentication and authorization utilities.

This module provides secure authentication mechanisms for communication
between Jerry's microservices and web chat authentication.
"""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import uuid4

import jwt
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from pydantic import Field

from .config import load_config

logger = logging.getLogger(__name__)


class UserSession(BaseModel):
    """User session model for web chat authentication."""

    user_id: str
    email: str
    authenticated_at: datetime
    expires_at: datetime | None = None
    permissions: dict[str, bool] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenManager:
    """JWT token manager for web chat authentication."""

    def __init__(self, config=None):
        """Initialize token manager."""
        self.config = config or load_config()
        self.secret_key = self.config.auth.secret_key or secrets.token_urlsafe(32)
        self.algorithm = self.config.auth.algorithm or "HS256"
        self.token_expiry = timedelta(hours=self.config.auth.token_expiry_hours or 24)

        if not self.config.auth.secret_key:
            logger.warning(
                "No secret key provided, using generated key (not persistent)"
            )

    def create_token(self, user_session: UserSession) -> str:
        """Create a JWT token for the user session."""
        now = datetime.utcnow()
        expires_at = now + self.token_expiry

        payload = {
            "sub": user_session.user_id,
            "email": user_session.email,
            "iat": now,
            "exp": expires_at,
            "authenticated_at": user_session.authenticated_at.isoformat(),
            "permissions": user_session.permissions,
            "metadata": user_session.metadata,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # Update session with expiry
        user_session.expires_at = expires_at

        logger.info(f"Created token for user {user_session.user_id}")
        return token

    def verify_token(self, token: str) -> UserSession:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Extract user session data
            user_session = UserSession(
                user_id=payload["sub"],
                email=payload["email"],
                authenticated_at=datetime.fromisoformat(payload["authenticated_at"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
                permissions=payload.get("permissions", {}),
                metadata=payload.get("metadata", {}),
            )

            # Check if token is expired
            if datetime.utcnow() > user_session.expires_at:
                raise jwt.ExpiredSignatureError("Token has expired")

            return user_session

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise ValueError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise ValueError("Token verification failed")


class ServiceAuthenticator:
    """Service-to-service authentication manager."""

    def __init__(self, service_name: str, config=None):
        """Initialize service authenticator.

        Args:
            service_name: Name of this service
            config: Configuration object (uses global if None)
        """
        self.service_name = service_name
        self.config = config or load_config()
        self.jwt_secret = self.config.security.jwt_secret
        self.api_key_header = self.config.security.api_key_header

        # Generate service-specific API key
        self.api_key = self._generate_service_api_key()

        logger.info(f"Initialized service authenticator for: {service_name}")

    def _generate_service_api_key(self) -> str:
        """Generate a unique API key for this service instance.

        Returns:
            Service API key
        """
        # Create deterministic but unique key based on service name and secret
        key_source = f"{self.service_name}:{self.jwt_secret}:{self.config.environment}"
        return hashlib.sha256(key_source.encode()).hexdigest()[:32]

    def create_service_token(
        self,
        target_service: str,
        expires_in_minutes: int = 30,
        additional_claims: dict | None = None,
    ) -> str:
        """Create a JWT token for service-to-service communication.

        Args:
            target_service: Name of the target service
            expires_in_minutes: Token expiration time in minutes
            additional_claims: Additional claims to include in token

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        exp = now + timedelta(minutes=expires_in_minutes)

        payload = {
            "iss": self.service_name,  # Issuer (this service)
            "aud": target_service,  # Audience (target service)
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "jti": str(uuid4()),  # JWT ID for tracking
            "type": "service_token",
            **(additional_claims or {}),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        logger.debug(
            f"Created service token for {self.service_name} -> {target_service}"
        )

        return token

    def verify_service_token(
        self, token: str, expected_issuer: str | None = None
    ) -> dict:
        """Verify a service JWT token.

        Args:
            token: JWT token to verify
            expected_issuer: Expected token issuer (service name)

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience=self.service_name,  # This service should be the audience
            )

            # Additional validation
            if payload.get("type") != "service_token":
                raise HTTPException(status_code=401, detail="Invalid token type")

            if expected_issuer and payload.get("iss") != expected_issuer:
                raise HTTPException(status_code=401, detail="Invalid token issuer")

            logger.debug(f"Verified service token from {payload.get('iss')}")
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def create_api_key_signature(self, request_data: str, timestamp: str) -> str:
        """Create HMAC signature for API key authentication.

        Args:
            request_data: Request data to sign
            timestamp: Request timestamp

        Returns:
            HMAC signature
        """
        message = f"{self.service_name}:{timestamp}:{request_data}"
        return hmac.new(
            self.api_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    def verify_api_key_signature(
        self, signature: str, request_data: str, timestamp: str, issuer_service: str
    ) -> bool:
        """Verify HMAC signature for API key authentication.

        Args:
            signature: Provided signature
            request_data: Request data
            timestamp: Request timestamp
            issuer_service: Name of the issuing service

        Returns:
            True if signature is valid
        """
        # Check timestamp freshness (within 5 minutes)
        try:
            req_time = float(timestamp)
            current_time = time.time()

            if abs(current_time - req_time) > 300:  # 5 minutes
                logger.warning(f"Request timestamp too old: {timestamp}")
                return False
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return False

        # Generate expected signature
        issuer_api_key = self._get_service_api_key(issuer_service)
        message = f"{issuer_service}:{timestamp}:{request_data}"
        expected_signature = hmac.new(
            issuer_api_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature, expected_signature)

    def _get_service_api_key(self, service_name: str) -> str:
        """Get API key for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Service API key
        """
        # Generate deterministic key for the service
        key_source = f"{service_name}:{self.jwt_secret}:{self.config.environment}"
        return hashlib.sha256(key_source.encode()).hexdigest()[:32]


class ServiceBearerAuth(HTTPBearer):
    """FastAPI dependency for service JWT authentication."""

    def __init__(self, service_name: str, expected_issuer: str | None = None):
        """Initialize service bearer auth.

        Args:
            service_name: Name of this service
            expected_issuer: Expected token issuer (optional)
        """
        super().__init__(auto_error=True)
        self.authenticator = ServiceAuthenticator(service_name)
        self.expected_issuer = expected_issuer

    async def __call__(self, request: Request) -> dict:
        """Authenticate service request.

        Args:
            request: FastAPI request object

        Returns:
            Decoded token payload
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        return self.authenticator.verify_service_token(
            credentials.credentials, self.expected_issuer
        )


class APIKeyAuth:
    """API key based authentication for service requests."""

    def __init__(self, service_name: str):
        """Initialize API key auth.

        Args:
            service_name: Name of this service
        """
        self.authenticator = ServiceAuthenticator(service_name)
        self.config = load_config()

    async def __call__(self, request: Request) -> str:
        """Authenticate API key request.

        Args:
            request: FastAPI request object

        Returns:
            Issuing service name
        """
        # Get headers
        api_key = request.headers.get(self.config.security.api_key_header)
        signature = request.headers.get("X-Signature")
        timestamp = request.headers.get("X-Timestamp")
        issuer = request.headers.get("X-Service-Name")

        if not all([api_key, signature, timestamp, issuer]):
            raise HTTPException(
                status_code=401, detail="Missing required authentication headers"
            )

        # Get request body for signature verification
        body = await request.body()
        request_data = body.decode() if body else ""

        # Verify signature
        if not self.authenticator.verify_api_key_signature(
            signature, request_data, timestamp, issuer
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

        logger.debug(f"Authenticated API key request from service: {issuer}")
        return issuer


class RoleBasedAuth:
    """Role-based access control for service endpoints."""

    def __init__(self, required_roles: list[str]):
        """Initialize role-based auth.

        Args:
            required_roles: List of roles required for access
        """
        self.required_roles = set(required_roles)

    def __call__(self, token_payload: dict) -> dict:
        """Check if token has required roles.

        Args:
            token_payload: Decoded JWT token payload

        Returns:
            Token payload if authorized
        """
        token_roles = set(token_payload.get("roles", []))

        if not self.required_roles.intersection(token_roles):
            raise HTTPException(
                status_code=403, detail=f"Required roles: {list(self.required_roles)}"
            )

        return token_payload


class RequestValidator:
    """Request validation and rate limiting."""

    def __init__(self, service_name: str):
        """Initialize request validator.

        Args:
            service_name: Name of this service
        """
        self.service_name = service_name
        self.config = load_config()
        self.request_counts: dict[str, list[float]] = {}

    def validate_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit.

        Args:
            client_id: Client identifier (service name or IP)

        Returns:
            True if within rate limit
        """
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []

        # Remove requests older than 1 minute
        self.request_counts[client_id] = [
            req_time
            for req_time in self.request_counts[client_id]
            if req_time > minute_ago
        ]

        # Check rate limit
        current_count = len(self.request_counts[client_id])
        if current_count >= self.config.security.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False

        # Add current request
        self.request_counts[client_id].append(now)
        return True

    async def __call__(self, request: Request) -> Request:
        """Validate incoming request.

        Args:
            request: FastAPI request object

        Returns:
            Request object if valid
        """
        # Get client identifier
        client_id = request.headers.get("X-Service-Name") or str(request.client.host)

        # Check rate limit
        if not self.validate_rate_limit(client_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        return request


def create_service_client_headers(
    service_name: str, target_service: str, request_data: str = ""
) -> dict[str, str]:
    """Create authentication headers for service-to-service requests.

    Args:
        service_name: Name of the calling service
        target_service: Name of the target service
        request_data: Request body data for signature

    Returns:
        Dictionary of authentication headers
    """
    authenticator = ServiceAuthenticator(service_name)
    timestamp = str(time.time())

    # Create signature
    signature = authenticator.create_api_key_signature(request_data, timestamp)

    return {
        authenticator.api_key_header: authenticator.api_key,
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "X-Service-Name": service_name,
        "Authorization": f"Bearer {authenticator.create_service_token(target_service)}",
    }


def verify_service_request(request_data: dict, expected_service: str) -> bool:
    """Simple helper to verify service request authenticity.

    Args:
        request_data: Request data with auth headers
        expected_service: Expected calling service name

    Returns:
        True if request is authentic
    """
    try:
        headers = request_data.get("headers", {})
        service_name = headers.get("X-Service-Name")

        if service_name != expected_service:
            return False

        # Additional verification could be added here
        return True

    except Exception as e:
        logger.error(f"Service request verification failed: {e}")
        return False
