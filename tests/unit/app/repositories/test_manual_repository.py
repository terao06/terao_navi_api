import pytest
from app.repositories.manual_repository import ManualRepository

class TestManualRepository:
    @pytest.mark.parametrize("company_id, application_id, expected_count", [
        (101, None, 1),
        (999, None, 0),
        (101, 101, 1),
        (101, 999, 0),
    ])
    def test_get_by_company_id(self, session, company_id, application_id, expected_count):
        result = ManualRepository.get_by_company_id(session, company_id, application_id)
        
        assert len(result) == expected_count

        if expected_count > 0:
            assert result[0].company_id == company_id
            if application_id:
                assert result[0].application_id == application_id
