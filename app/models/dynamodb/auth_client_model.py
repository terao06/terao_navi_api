import os

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection


class CompanyIdIndex(GlobalSecondaryIndex):
    """
    GSI: idx_company_id
      - hash key: company_id (Number)
      - projection: ALL
    """
    class Meta:
        index_name = "idx_company_id"
        projection = AllProjection()

    company_id = NumberAttribute(hash_key=True)


class AuthClientModel(Model):
    """
    DynamoDB: auth_clients
      - PK: client_id (S)
      - GSI: idx_company_id (company_id N)
    """
    class Meta:
        table_name = "auth_clients"
        region = "ap-northeast-1"
        host = os.getenv("DDB_ENDPOINT")
        billing_mode = "PAY_PER_REQUEST"

    client_id = UnicodeAttribute(hash_key=True)
    company_id = NumberAttribute(null=False)
    secret_hash = UnicodeAttribute(null=False)
    is_active = NumberAttribute(default=1)
    created_at = UnicodeAttribute(null=False)
    home_page = UnicodeAttribute(null=False)
    idx_company_id = CompanyIdIndex()
