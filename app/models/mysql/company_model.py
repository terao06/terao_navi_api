from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from app.core.database.mysql import Base


class CompanyModel(Base):
    __tablename__ = 'companies'
    
    company_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='会社名')
    address = Column(String(255), nullable=False, comment='住所')
    tel = Column(String(255), nullable=False, comment='電話番号')
    home_page = Column(String(255), nullable=False, comment='ホームページURL')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='削除フラグ')
    deleted_at = Column(DateTime, nullable=True, comment='削除日時')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='作成日時')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新日時')

    # Relationships
    users = relationship("UserModel", back_populates="companies")
    applications = relationship("ApplicationModel", back_populates="companies")
