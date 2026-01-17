import sys
from app.core.utils.credential_util import CredentialUtil
try:
    client_id, client_secret, secret_hash = CredentialUtil.generate_client_credential()
    # 標準出力: client_id client_secret secret_hash（スペース区切り）
    print(f'{client_id} {client_secret} {secret_hash}')
except Exception as e:
    print(e, file=sys.stderr)
    sys.exit(1)
