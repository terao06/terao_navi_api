from datetime import datetime
from pydantic import BaseModel, Field


class AccessTokenResponse(BaseModel):
    access_token: str = Field(..., description="短命アクセス用のトークン")
    expires_at: datetime = Field(..., description="トークンの有効期限 (UTC)")
    ttl_seconds: int = Field(..., description="トークンの有効時間（秒）")
    refresh_token: str = Field(..., description="アクセストークン更新用のリフレッシュトークン")
    refresh_expires_at: datetime = Field(..., description="リフレッシュトークンの有効期限 (UTC)")
    refresh_ttl_seconds: int = Field(..., description="リフレッシュトークンの有効時間（秒）")
