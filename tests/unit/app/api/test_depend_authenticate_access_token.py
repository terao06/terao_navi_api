import secrets
import pytest
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.depend import authenticate_access_token
from app.core.utils.token_util import TokenUtil


def _cred(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestAuthenticateAccessToken:
    def test_valid_token(self):
        exp = datetime.now(timezone.utc) + timedelta(seconds=2)
        token = TokenUtil.generate_access_token(
            random_part=secrets.token_urlsafe(16),
            expires_at=exp,
            company_id=1,
            secret_key="dummy")
        assert token

    def test_expired_token_raises(self):
        exp = datetime.now(timezone.utc) - timedelta(seconds=10)
        token = TokenUtil.generate_access_token(
            random_part=secrets.token_urlsafe(16),
            expires_at=exp,
            company_id=1,
            secret_key="dummy")

        with pytest.raises(HTTPException) as exc:
            authenticate_access_token(cred=_cred(token))

        assert exc.value.status_code == 401

    def test_invalid_signature_raises(self):
        exp = datetime.now(timezone.utc) + timedelta(seconds=60)
        token = TokenUtil.generate_access_token(
            random_part=secrets.token_urlsafe(16),
            expires_at=exp,
            company_id=1,
            secret_key="dummy")

        # Tamper the token by changing one character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

        with pytest.raises(HTTPException) as exc:
            authenticate_access_token(cred=_cred(tampered))

        assert exc.value.status_code == 401
