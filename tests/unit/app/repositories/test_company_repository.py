import pytest
from sqlalchemy.orm import Session

from app.repositories.company_repository import CompanyRepository
from app.models.mysql.company_model import CompanyModel


class TestCompanyRepository:
    @pytest.mark.parametrize(
        "company_id, expected_name, expected_address, expected_tel, should_exist",
        [
            (101, "Test Company", "Tokyo", "03-1234-5678", True),  # 正常系
            (99999, None, None, None, False),  # 存在しないID
            (102, None, None, None, False),  # 削除済み
        ],
    )
    def test_get_by_company_id(
        self,
        session: Session,
        company_id: int,
        expected_name: str | None,
        expected_address: str | None,
        expected_tel: str | None,
        should_exist: bool,
    ):
        """get_by_company_idのテスト"""
        result = CompanyRepository.get_by_company_id(session, company_id=company_id)

        if should_exist:
            assert isinstance(result, CompanyModel)
            assert result.company_id == company_id
            assert result.name == expected_name
            assert result.address == expected_address
            assert result.tel == expected_tel
            assert result.deleted_at is None
        else:
            assert result is None
