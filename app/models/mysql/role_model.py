from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from app.core.database.mysql import Base

class RoleModel(Base):
    __tablename__ = 'roles'

    FULL_ACCESS = 1
    LIMITED_ACCESS = 2
    READ_ONLY = 3

    role_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, comment='ロール名')
    description = Column(Text, nullable=True, comment='説明')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='作成日時')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新日時')

    # Relationships
    users = relationship("UserModel", back_populates="roles")
