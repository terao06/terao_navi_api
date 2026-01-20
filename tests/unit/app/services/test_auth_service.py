import re
from datetime import datetime, timezone

import pytest

from app.services.auth_service import AuthService
from app.models.responses.access_token_response import AccessTokenResponse


class TestAuthService:
    def test_get_auth_token_returns_valid_response(self):
        service = AuthService()

        token_response = service.get_auth_token()

        # Type and model
        assert isinstance(token_response, AccessTokenResponse)

        # Required fields exist and have correct types
        assert isinstance(token_response.access_token, str) and token_response.access_token
        assert isinstance(token_response.refresh_token, str) and token_response.refresh_token
        assert isinstance(token_response.ttl_seconds, int) and token_response.ttl_seconds == 5 * 60
        assert (
            isinstance(token_response.refresh_ttl_seconds, int)
            and token_response.refresh_ttl_seconds == 60 * 60
        )
        assert isinstance(token_response.expires_at, datetime)
        assert isinstance(token_response.refresh_expires_at, datetime)

        # Datetimes should be timezone-aware UTC
        assert token_response.expires_at.tzinfo is not None
        assert token_response.refresh_expires_at.tzinfo is not None
        assert token_response.expires_at.utcoffset() == timezone.utc.utcoffset(token_response.expires_at)
        assert token_response.refresh_expires_at.utcoffset() == timezone.utc.utcoffset(token_response.refresh_expires_at)

        # Expiration should be roughly now + ttl (allowing small processing skew)
        now_utc = datetime.now(timezone.utc)
        delta_access = token_response.expires_at - now_utc
        delta_refresh = token_response.refresh_expires_at - now_utc

        # Allow up to ~3 seconds skew
        assert 0 < delta_access.total_seconds() <= token_response.ttl_seconds + 3
        assert 0 < delta_refresh.total_seconds() <= token_response.refresh_ttl_seconds + 3

    def test_tokens_are_urlsafe_and_unique(self):
        service = AuthService()

        r1 = service.get_auth_token()
        r2 = service.get_auth_token()

        # Tokens should be different between calls
        assert r1.access_token != r2.access_token
        assert r1.refresh_token != r2.refresh_token

        # token_urlsafe should produce URL-safe characters (RFC 3986 unreserved)
        # Using a permissive check: letters, digits, '-', '.', '_', '~'
        urlsafe_pattern = re.compile(r"^[A-Za-z0-9\-\._~]+$")
        assert urlsafe_pattern.match(r1.access_token) is not None
        assert urlsafe_pattern.match(r1.refresh_token) is not None
        assert urlsafe_pattern.match(r2.access_token) is not None
        assert urlsafe_pattern.match(r2.refresh_token) is not None

    def test_refresh_auth_token_returns_valid_response(self):
        service = AuthService()

        token_response = service.refresh_auth_token(company_id=123)

        # Type and model
        assert isinstance(token_response, AccessTokenResponse)

        # Required fields exist and have correct types
        assert isinstance(token_response.access_token, str) and token_response.access_token
        assert isinstance(token_response.refresh_token, str) and token_response.refresh_token
        assert isinstance(token_response.ttl_seconds, int) and token_response.ttl_seconds == 5 * 60
        assert (
            isinstance(token_response.refresh_ttl_seconds, int)
            and token_response.refresh_ttl_seconds == 60 * 60
        )
        assert isinstance(token_response.expires_at, datetime)
        assert isinstance(token_response.refresh_expires_at, datetime)

        # Datetimes should be timezone-aware UTC
        assert token_response.expires_at.tzinfo is not None
        assert token_response.refresh_expires_at.tzinfo is not None
        assert token_response.expires_at.utcoffset() == timezone.utc.utcoffset(token_response.expires_at)
        assert token_response.refresh_expires_at.utcoffset() == timezone.utc.utcoffset(token_response.refresh_expires_at)

        # Expiration should be roughly now + ttl (allowing small processing skew)
        now_utc = datetime.now(timezone.utc)
        delta_access = token_response.expires_at - now_utc
        delta_refresh = token_response.refresh_expires_at - now_utc

        # Allow up to ~3 seconds skew
        assert 0 < delta_access.total_seconds() <= token_response.ttl_seconds + 3
        assert 0 < delta_refresh.total_seconds() <= token_response.refresh_ttl_seconds + 3

    def test_refresh_tokens_are_urlsafe_and_unique(self):
        service = AuthService()

        r1 = service.refresh_auth_token(company_id=123)
        r2 = service.refresh_auth_token(company_id=123)

        # Tokens should be different between calls
        assert r1.access_token != r2.access_token
        assert r1.refresh_token != r2.refresh_token

        # token_urlsafe should produce URL-safe characters (RFC 3986 unreserved)
        urlsafe_pattern = re.compile(r"^[A-Za-z0-9\-\._~]+$")
        assert urlsafe_pattern.match(r1.access_token) is not None
        assert urlsafe_pattern.match(r1.refresh_token) is not None
        assert urlsafe_pattern.match(r2.access_token) is not None
        assert urlsafe_pattern.match(r2.refresh_token) is not None
