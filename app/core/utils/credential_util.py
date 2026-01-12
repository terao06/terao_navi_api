import secrets
import hashlib


class CredentialUtil:
    @classmethod
    def generate_client_credential(cls) -> str:
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
    def decrypt_client_credential(cls, client_secret: str):
        return hashlib.sha256(client_secret.encode()).hexdigest()
