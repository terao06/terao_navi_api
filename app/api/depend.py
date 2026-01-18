from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from app.core.utils.credential_util import CredentialUtil
from app.models.dynamodb.auth_client_model import AuthClientModel
from app.core.utils.token_util import TokenUtil
from datetime import datetime, timezone
from app.core.logging import NaviApiLog
from app.core.aws.secret_manager import SecretManager


bearer = HTTPBearer(auto_error=False)
basic = HTTPBasic(auto_error=False)


def require_api_key(
    request: Request,
    cred: HTTPBasicCredentials = Depends(basic),
) -> AuthClientModel:

    origin = request.headers.get("X-Origin", None)

    if cred is None:
        NaviApiLog.warning(
            "認証情報が存在しません。"
        )
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    try:
        client_id = cred.username
        client_secret = cred.password
    except ValueError:
        NaviApiLog.warning(
            "クレデンシャルの取得に失敗しました。"
        )
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    secret_hash = CredentialUtil.decrypt_client_credential(client_secret=client_secret)

    try:
        client = AuthClientModel.get(client_id)
    except AuthClientModel.DoesNotExist:
        NaviApiLog.warning(
            f"認証情報が存在しません: client_id={client_id}"
        )
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    if client.secret_hash != secret_hash:
        NaviApiLog.warning("hash値が一致しません。")
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    if client.is_active != True:
        NaviApiLog.warning(f"対象の認証情報は使用できません。 client_id={client_id}")
        raise HTTPException(status_code=403, detail="認証に失敗しました。")
    if client.home_page != origin:
        NaviApiLog.warning(f"ホームページが一致しません。 "
                           f"client_id={client_id} "
                           f"home_page={client.home_page}")

        raise HTTPException(status_code=403, detail="認証に失敗しました。")

    return client


def authenticate_access_token(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    """
    Authorization ヘッダの Bearer トークン（短命アクセス用の access_token）を検証します。

    現在の実装では、トークンの形式（URL セーフ文字で構成）と存在のみを検証します。
    追加の永続化や失効管理（例: DynamoDB/Redis に保存して TTL/ワンタイム消費を検証）を導入する場合は、
    DBにトークンを保存しそれと比較する使用を入れて過去のトークンを使えないようにする必要あり。

    Returns:
        int: 正常な場合は company_id を返却します。

    Raises:
        HTTPException: トークンが存在しない、形式が不正、その他検証に失敗した場合は 401 を返します。
    """
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    token = cred.credentials

    token_settings = SecretManager().get_secret("token_setting")
    access_secret = token_settings.get("access_token_secret") if isinstance(token_settings, dict) else None

    is_valid, exp_epoch = TokenUtil.verify_access_token(token, access_secret)
    if not is_valid or exp_epoch is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if now_epoch > exp_epoch:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。")
    
    company_id = TokenUtil.extract_company_id(token)
    if company_id is None:
        # company_id がトークンに含まれていない場合は認証エラー
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

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

    token_settings = SecretManager().get_secret("token_setting")
    refresh_secret = token_settings.get("refresh_token_secret", None)

    is_valid, exp_epoch = TokenUtil.verify_refresh_token(token, refresh_secret)
    if not is_valid or exp_epoch is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました。")

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if now_epoch > exp_epoch:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。")

    company_id = TokenUtil.extract_company_id(token)
    if company_id is None:
        raise HTTPException(status_code=401, detail="認証に失敗しました（company_id がトークンに含まれていません）。")

    return company_id
