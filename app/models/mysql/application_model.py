from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func


from app.core.database.mysql import Base


class ApplicationModel(Base):
    __tablename__ = 'applications'

    application_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False, comment='会社ID')
    application_name = Column(String(255), nullable=False, comment='アプリケーション名')
    description = Column(Text, nullable=True, comment='説明')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='削除フラグ')
    deleted_at = Column(DateTime, nullable=True, comment='削除日時')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='作成日時')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新日時')

    # Relationships
    companies = relationship("CompanyModel", back_populates="applications")
    manuals = relationship("ManualModel", back_populates="applications")
