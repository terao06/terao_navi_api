from app.models.mysql.company_model import CompanyModel
from sqlalchemy.orm import Session


class CompanyRepository:
    @classmethod
    def get_by_company_id(
        cls,
        session: Session,
        company_id: int,
    ) -> CompanyModel | None:
        return session.query(
            CompanyModel
        ).filter(
            CompanyModel.company_id == company_id,
            CompanyModel.deleted_at.is_(None)
        ).first()
