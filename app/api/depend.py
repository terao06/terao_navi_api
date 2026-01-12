from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.utils.credential_util import CredentialUtil
from app.models.dynamodb.auth_client_model import AuthClientModel


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
