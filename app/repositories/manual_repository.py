from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.mysql.company_model import CompanyModel
from app.models.mysql.application_model import ApplicationModel
from app.models.mysql.manual_model import ManualModel


@dataclass
class ManualDto:
    company_id: int
    application_id: int
    manual_id: int
    file_extension: str


class ManualRepository:
    @classmethod
    def get_by_company_id(
        cls,
        session: Session,
        company_id: int,
        application_id: int|None=None,
    ) -> list[ManualDto]:
        query = session.query(
            CompanyModel.company_id,
            ApplicationModel.application_id,
            ManualModel.manual_id,
            ManualModel.file_extension
        ).join(
            ApplicationModel, CompanyModel.company_id == ApplicationModel.company_id
        ).join(
            ManualModel, ApplicationModel.application_id == ManualModel.application_id
        ).filter(
            CompanyModel.company_id == company_id,
            CompanyModel.deleted_at.is_(None),
            ApplicationModel.deleted_at.is_(None),
            ManualModel.deleted_at.is_(None)
        )
        if application_id:
            query = query.filter(
                ApplicationModel.application_id == application_id
            )
        manuals = query.all()

        manual_dtos = []
        for manual in manuals:
            manual_dtos.append(
                ManualDto(
                    company_id=manual.company_id,
                    application_id=manual.application_id,
                    manual_id=manual.manual_id,
                    file_extension=manual.file_extension
                    
                )
            )
        return manual_dtos
