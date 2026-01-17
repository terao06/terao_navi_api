import secrets
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from app.api.depend import authenticate_refresh_token
from app.core.utils.token_util import TokenUtil
from fastapi.security import HTTPAuthorizationCredentials


def _cred(token: str) -> HTTPAuthorizationCredentials:
    # Simulate Authorization: Bearer <token>
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_authenticate_refresh_token_valid():
    company_id = 123
    exp = datetime.now(timezone.utc) + timedelta(seconds=60)
    token = TokenUtil.generate_refresh_token(secrets.token_urlsafe(16), exp, company_id=company_id)
    result = authenticate_refresh_token(cred=_cred(token))
    assert result == company_id


def test_authenticate_refresh_token_expired_raises():
    company_id = 1
    exp = datetime.now(timezone.utc) - timedelta(seconds=1)
    token = TokenUtil.generate_refresh_token(secrets.token_urlsafe(16), exp, company_id=company_id)
    with pytest.raises(HTTPException):
        authenticate_refresh_token(cred=_cred(token))


def test_authenticate_refresh_token_tampered_raises():
    company_id = 1
    exp = datetime.now(timezone.utc) + timedelta(seconds=60)
    token = TokenUtil.generate_refresh_token(secrets.token_urlsafe(16), exp, company_id=company_id)
    # Tamper with token by changing a character
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(HTTPException):
        authenticate_refresh_token(cred=_cred(tampered))
