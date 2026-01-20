import json
import pytest
from botocore.exceptions import ClientError
from app.core.aws.ssm_client import SsmClient

class TestSsmClient:
    @pytest.mark.parametrize("param_name, raw_value, expected_value", [
        ("test-json-param", json.dumps({"key": "value", "number": 123}), {"key": "value", "number": 123}),
        ("test-string-param", "plain-text-value", "plain-text-value"),
    ])
    def test_get_parameter_success(self, managed_parameter, param_name, raw_value, expected_value):
        """パラメータ取得の成功ケース（JSON/文字列）（LocalStack連携）"""
        with managed_parameter(param_name, raw_value):
            client = SsmClient()
            result = client.get_parameter(param_name)
            assert result == expected_value

    def test_get_parameter_error(self):
        """存在しないパラメータでのエラーハンドリング（LocalStack連携）"""
        client = SsmClient()
        with pytest.raises(ClientError) as excinfo:
            client.get_parameter("non-existent-param-999")

        assert excinfo.value.response["Error"]["Code"] == "ParameterNotFound"
