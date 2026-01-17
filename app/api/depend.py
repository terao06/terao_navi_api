from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.utils.credential_util import CredentialUtil
from app.models.dynamodb.auth_client_model import AuthClientModel
from app.core.utils.token_util import TokenUtil
from datetime import datetime, timezone


bearer = HTTPBearer(auto_error=False)


def require_api_key(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> AuthClientModel:
    if cred is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    try:
        client_id, client_secret = cred.credentials.split(":", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    secret_hash = CredentialUtil.decrypt_client_credential(client_secret=client_secret)

    try:
        client = AuthClientModel.get(client_id)
    except AuthClientModel.DoesNotExist:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    if client.secret_hash != secret_hash:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    if client.is_active != True:
        raise HTTPException(status_code=403, detail="認証に失敗しました。")

    return client


def authenticate_access_token(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    """
    Authorization ヘッダの Bearer トークン（短命アクセス用の access_token）を検証します。

    現在の実装では、トークンの形式（URL セーフ文字で構成）と存在のみを検証します。
    追加の永続化や失効管理（例: DynamoDB/Redis に保存して TTL/ワンタイム消費を検証）を導入する場合は、
    ここでストレージ照会や失効チェックを行ってください。

    Returns:
        str: 正常な場合は access_token を返却します。

    Raises:
        HTTPException: トークンが存在しない、形式が不正、その他検証に失敗した場合は 401 を返します。
    """
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    token = cred.credentials

    # Verify signature and extract expiry
    is_valid, exp_epoch = TokenUtil.verify_access_token(token)
    if not is_valid or exp_epoch is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if now_epoch > exp_epoch:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。")
    
    company_id = TokenUtil.extract_company_id(token)
    if company_id is None:
        # company_id がトークンに含まれていない場合は認証エラー
        raise HTTPException(status_code=401, detail="認証に失敗しました（company_id がトークンに含まれていません）。")

    return company_id


def authenticate_refresh_token(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    """
    Authorization ヘッダの Bearer リフレッシュトークンを検証します。

    - 署名検証（REFRESH_TOKEN_SECRET を使用）
    - 有効期限の確認
    - company_id の抽出（トークン埋め込み）

    Returns:
        int: 正常な場合は company_id を返却します。

    Raises:
        HTTPException: トークンが存在しない、形式が不正、有効期限切れ、その他検証に失敗した場合は 401 を返します。
    """
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    token = cred.credentials

    # Verify signature and extract expiry
    is_valid, exp_epoch = TokenUtil.verify_refresh_token(token)
    if not is_valid or exp_epoch is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if now_epoch > exp_epoch:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。")

    company_id = TokenUtil.extract_company_id(token)
    if company_id is None:
        # company_id がトークンに含まれていない場合は認証エラー
        raise HTTPException(status_code=401, detail="認証に失敗しました（company_id がトークンに含まれていません）。")

    return company_id
