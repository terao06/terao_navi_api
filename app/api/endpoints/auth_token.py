from fastapi import APIRouter
from fastapi import Depends
from app.api.depend import require_api_key
from app.middlewares.request_wrapper import request_rapper
from app.middlewares.response_wrapper import response_rapper
from app.services.auth_service import AuthService
from app.api.depend import authenticate_refresh_token
from app.core.logging import NaviApiLog

token_router = APIRouter()


@token_router.post("/auth/token")
@response_rapper()
@request_rapper()
def read_root(
    company_id: int = Depends(require_api_key)):
    """
    トークンの発行を行います。
    """
    NaviApiLog.info("トークン発効を行います")
    return AuthService().get_auth_token(company_id=company_id)


@token_router.post("/auth/refresh")
@response_rapper()
@request_rapper()
def refresh_token(company_id: int = Depends(authenticate_refresh_token)):
    """
    新しいアクセストークンとリフレッシュトークンを発行します。
    """
    NaviApiLog.info("新しいトークン発効を行います")
    return AuthService().refresh_auth_token(company_id=company_id)
