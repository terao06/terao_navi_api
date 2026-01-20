import json
import sys
import pytest
from botocore.exceptions import ClientError
from app.core.aws.secret_manager import SecretManager


class TestSecretManager:
    def test_get_secret_json(self, managed_secret):
        """JSON形式のシークレット取得（LocalStack連携）"""

        secret_name = "test-json-secret"
        secret_data = {"key": "value", "number": 123}

        with managed_secret(secret_name, json.dumps(secret_data)):
            # テスト対象の実行（モックなし）
            sm = SecretManager()
            result = sm.get_secret(secret_name)

            assert result == secret_data

    def test_get_secret_string(self, managed_secret):
        """文字列形式のシークレット取得（LocalStack連携）"""
        secret_name = "test-string-secret"
        secret_string = "plain-text-password"

        with managed_secret(secret_name, secret_string):
            sm = SecretManager()
            result = sm.get_secret(secret_name)
    
            assert result == secret_string

    def test_get_secret_binary(self, managed_secret):
        """バイナリ形式のシークレット取得（LocalStack連携）"""
        secret_name = "test-binary-secret"
        secret_binary = b"\x01\x02\x03\x04"

        with managed_secret(secret_name, secret_binary):
            sm = SecretManager()
            result = sm.get_secret(secret_name)
    
            assert result == secret_binary

    def test_get_secret_not_found(self):
        """存在しないシークレットでのエラーハンドリング（LocalStack連携）"""
        sm = SecretManager()
        with pytest.raises(ClientError) as excinfo:
            sm.get_secret("non-existent-secret-999")

        assert excinfo.value.response["Error"]["Code"] == "ResourceNotFoundException"
