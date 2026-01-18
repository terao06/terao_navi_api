from app.core.aws.secret_manager import SecretManager
from app.models.responses.access_token_response import AccessTokenResponse
import secrets
from datetime import datetime, timedelta, timezone
from app.core.utils.token_util import TokenUtil


class AuthService:
    def __init__(self):
        self.params = SecretManager().get_secret("token_setting")

    def get_auth_token(self, company_id: int | None = None) -> AccessTokenResponse:
        ttl_seconds = self.params.get("ttl_seconds")
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        refresh_ttl_seconds = self.params.get("refresh_ttl_seconds")
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(seconds=refresh_ttl_seconds)

        random_part = secrets.token_urlsafe(24)
        access_token = TokenUtil.generate_access_token(
            random_part=random_part,
            expires_at=expires_at,
            company_id=company_id,
            secret_key=self.params.get("access_token_secret")
        )

        refresh_random = secrets.token_urlsafe(24)
        refresh_token = TokenUtil.generate_refresh_token(
            random_part=refresh_random,
            expires_at=refresh_expires_at,
            company_id=company_id if company_id is not None else 0,
            refresh_secret_key=self.params.get("refresh_token_secret")
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
        ttl_seconds = self.params.get("ttl_seconds")
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        access_token = TokenUtil.generate_access_token(
            random_part=secrets.token_urlsafe(24),
            expires_at=expires_at,
            company_id=company_id,
            secret_key=self.params.get("access_token_secret")
        )

        refresh_ttl_seconds = self.params.get("refresh_ttl_seconds")
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(seconds=refresh_ttl_seconds)
        refresh_token = TokenUtil.generate_refresh_token(
            random_part=secrets.token_urlsafe(24),
            expires_at=refresh_expires_at,
            company_id=company_id,
            refresh_secret_key=self.params.get("refresh_token_secret")
        )

        return AccessTokenResponse(
            access_token=access_token,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds,
            refresh_token=refresh_token,
            refresh_expires_at=refresh_expires_at,
            refresh_ttl_seconds=refresh_ttl_seconds,
        )
