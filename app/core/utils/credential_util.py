import base64
import secrets
import hashlib


class CredentialUtil:
    @classmethod
    def generate_client_credential(cls) -> tuple[str, str, str]:
        """
        クライアントIDとシークレットを生成
        
        Returns:
            tuple: (client_id, client_secret, secret_hash)
        """
        client_id = secrets.token_hex(16)

        client_secret = secrets.token_hex(32)

        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
        
        return client_id, client_secret, secret_hash
    
    @classmethod
    def decode_basic_credential(cls, encoded: str) -> tuple[str, str]:
        try:
            raw = base64.b64decode(encoded).decode("utf-8")
            client_id, client_secret = raw.split(":", 1)
            return client_id, client_secret
        except:
            raise ValueError("クレデンシャルの取得に失敗しました。")

    @classmethod
    def encode_basic_credential(cls, client_id: str, client_secret: str) -> str:
        raw = f"{client_id}:{client_secret}".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")

    @classmethod
    def decrypt_client_credential(cls, client_secret: str):
        return hashlib.sha256(client_secret.encode()).hexdigest()
