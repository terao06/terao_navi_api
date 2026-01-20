from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from app.core.aws.secret_manager import SecretManager


Base = declarative_base()


class MySQLDatabase:
    def __init__(self):
        self._engine = None
        self._session_local = None

    def initialize(self):
        params = SecretManager().get_secret("mysql_setting")

        SQLALCHEMY_DATABASE_URL = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8".format(
            params.get("user"),
            params.get("password"),
            params.get("host"),
            params.get("port"),
            params.get("database")
        )

        self._engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=params.get("pool_size"),
            max_overflow=params.get("max_overflow"),
            pool_timeout=params.get("pool_timeout"),
            pool_recycle=params.get("pool_recycle"),
            pool_pre_ping=params.get("pool_pre_ping"),
        )

        self._session_local = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    @property
    def engine(self):
        if self._engine is None:
            self.initialize()
        return self._engine

    @property
    def session_local(self):
        if self._session_local is None:
            self.initialize()
        return self._session_local

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        if self._session_local is None:
            self.initialize()
        
        db = self._session_local()
        try:
            yield db
        finally:
            db.close()
