import boto3
import json
import os
from botocore.exceptions import ClientError
from typing import Dict, Any, Union

class SecretManager:
    def __init__(self):
        """
        Secrets Manager クライアントの初期化
        """
        self.region_name = os.getenv("AWS_REGION", "ap-northeast-1")
        self.endpoint_url = os.getenv("SECRETS_MANAGER_ENDPOINT")

        self.client = boto3.client(
            service_name='secretsmanager',
            region_name=self.region_name,
            endpoint_url=self.endpoint_url
        )

    def get_secret(self, secret_name: str) -> Union[Dict[str, Any], str, bytes]:
        """
        指定されたシークレット名で値を取得する。
        JSON形式の場合は辞書型にパースして返す。
        """
        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # 必要に応じてログ出力や例外の再送出を行う
            raise e

        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            try:
                return json.loads(secret)
            except json.JSONDecodeError:
                return secret
        else:
            return get_secret_value_response['SecretBinary']
