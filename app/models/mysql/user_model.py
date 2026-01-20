from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from app.models.mysql.role_model import RoleModel

from app.core.database.mysql import Base


class UserModel(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False, comment='会社ID')
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False, default=RoleModel.READ_ONLY, comment='ロールID')
    username = Column(String(150), unique=True, nullable=False, comment='ユーザー名')
    email = Column(String(255), nullable=False, comment='メールアドレス')
    password = Column(String(255), nullable=False, comment='パスワード')
    first_name = Column(String(150), nullable=True, comment='名')
    last_name = Column(String(150), nullable=True, comment='姓')
    is_active = Column(Boolean, default=True, nullable=False, comment='有効')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='削除フラグ')
    deleted_at = Column(DateTime, nullable=True, comment='削除日時')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='作成日時')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新日時')

    # Relationships
    companies = relationship("CompanyModel", back_populates="users")
    roles = relationship("RoleModel", back_populates="users")
