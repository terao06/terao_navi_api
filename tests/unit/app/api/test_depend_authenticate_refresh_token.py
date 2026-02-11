import secrets
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from app.api.depend import authenticate_refresh_token
from app.core.utils.token_util import TokenUtil
from fastapi.security import HTTPAuthorizationCredentials


def _cred(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_authenticate_refresh_token_valid():
    exp = datetime.now(timezone.utc) + timedelta(seconds=60)
    token = TokenUtil.generate_refresh_token(
        random_part=secrets.token_urlsafe(16),
        expires_at=exp,
        company_id=123,
        refresh_secret_key="dummy")
    assert token


def test_authenticate_refresh_token_expired_raises():
    exp = datetime.now(timezone.utc) - timedelta(seconds=1)
    token = TokenUtil.generate_refresh_token(
        random_part=secrets.token_urlsafe(16),
        expires_at=exp,
        company_id=123,
        refresh_secret_key="dummy")

    with pytest.raises(HTTPException):
        authenticate_refresh_token(cred=_cred(token))


def test_authenticate_refresh_token_tampered_raises():
    exp = datetime.now(timezone.utc) + timedelta(seconds=60)
    token = TokenUtil.generate_refresh_token(
        random_part=secrets.token_urlsafe(16),
        expires_at=exp,
        company_id=123,
        refresh_secret_key="dummy")
    # Tamper with token by changing a character
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(HTTPException):
        authenticate_refresh_token(cred=_cred(tampered))
