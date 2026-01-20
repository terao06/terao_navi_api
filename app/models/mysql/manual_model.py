from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from app.core.database.mysql import Base


class ManualModel(Base):
    __tablename__ = 'manuals'

    manual_id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.application_id', ondelete='CASCADE'), nullable=False, comment='アプリケーションID')
    manual_name = Column(String(200), nullable=False, comment='マニュアル名')
    description = Column(Text, nullable=True, comment='説明')
    file_extension = Column(String(500), nullable=False, comment='ファイル拡張子')
    file_size = Column(BigInteger, nullable=True, comment='ファイルサイズ(bytes)')
    is_deleted = Column(Boolean, default=False, nullable=False, comment='削除フラグ')
    deleted_at = Column(DateTime, nullable=True, comment='削除日時')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='作成日時')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新日時')

    # Relationships
    applications = relationship("ApplicationModel", back_populates="manuals")
