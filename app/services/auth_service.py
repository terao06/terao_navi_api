from app.models.responses.access_token_response import AccessTokenResponse
import secrets
from datetime import datetime, timedelta, timezone
from app.core.utils.token_util import TokenUtil


class AuthService:
    def get_auth_token(self, company_id: int | None = None) -> AccessTokenResponse:
        ttl_seconds = 5 * 60
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        refresh_ttl_seconds = 60 * 60
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(seconds=refresh_ttl_seconds)

        # Embed expiry and sign the token to enable verification without persistence
        random_part = secrets.token_urlsafe(24)
        access_token = TokenUtil.generate_access_token(
            random_part=random_part,
            expires_at=expires_at,
            company_id=company_id,
        )
        # Use signed refresh token with embedded company_id and expiry
        refresh_random = secrets.token_urlsafe(24)
        refresh_token = TokenUtil.generate_refresh_token(
            random_part=refresh_random,
            expires_at=refresh_expires_at,
            company_id=company_id if company_id is not None else 0,
        )

        return AccessTokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
            refresh_ttl_seconds=refresh_ttl_seconds,
        )

    def refresh_auth_token(self, company_id: int) -> AccessTokenResponse:
        """
        Issue a new access token and rotated refresh token for an already authenticated company.
        No authentication or token verification is performed here.
        """
        ttl_seconds = 5 * 60
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        access_token = TokenUtil.generate_access_token(
            random_part=secrets.token_urlsafe(24),
            expires_at=expires_at,
            company_id=company_id,
        )

        refresh_ttl_seconds = 60 * 60
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(seconds=refresh_ttl_seconds)
        refresh_token = TokenUtil.generate_refresh_token(
            random_part=secrets.token_urlsafe(24),
            expires_at=refresh_expires_at,
            company_id=company_id,
        )

        return AccessTokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
            refresh_ttl_seconds=refresh_ttl_seconds,
        )
