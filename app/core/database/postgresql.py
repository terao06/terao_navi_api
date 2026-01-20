from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from app.core.aws.secret_manager import SecretManager
from app.core.logging import NaviApiLog

Base = declarative_base()


class PostgreSQLDatabase:
    """
    PostgreSQL接続を管理するクラス。
    コネクションプーリングとセッション管理を提供します。
    """
    
    def __init__(self):
        self._engine = None
        self._session_local = None
        self._connection_string = None

    def initialize(self):
        """
        PostgreSQL接続を初期化します。
        Secrets Managerから設定を取得し、SQLAlchemy Engineを作成します。
        """
        try:
            params = SecretManager().get_secret("postgresql_setting")
            
            if not params:
                raise ValueError("postgresql_setting is not configured in Secrets Manager")
            
            # 必須パラメータの検証
            required_keys = ["user", "password", "host", "port", "database"]
            missing_keys = [key for key in required_keys if not params.get(key)]
            if missing_keys:
                raise ValueError(f"Missing required PostgreSQL settings: {', '.join(missing_keys)}")
            
            # 接続文字列の構築
            self._connection_string = "postgresql+psycopg://{0}:{1}@{2}:{3}/{4}".format(
                params.get("user"),
                params.get("password"),
                params.get("host"),
                params.get("port"),
                params.get("database"),
            )
            
            # Engine作成時のオプション設定
            engine_options = {
                "pool_size": params.get("pool_size", 5),
                "max_overflow": params.get("max_overflow", 10),
                "pool_timeout": params.get("pool_timeout", 30),
                "pool_recycle": params.get("pool_recycle", 3600),
                "pool_pre_ping": params.get("pool_pre_ping", True),
            }
            
            self._engine = create_engine(self._connection_string, **engine_options)
            self._session_local = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            
            NaviApiLog.info("PostgreSQL connection initialized successfully")
            
        except Exception as e:
            NaviApiLog.error(f"Failed to initialize PostgreSQL connection: {e}")
            raise

    @property
    def engine(self):
        """
        SQLAlchemy Engineを取得します。
        初期化されていない場合は自動的に初期化します。
        """
        if self._engine is None:
            self.initialize()
        return self._engine

    @property
    def session_local(self):
        """
        SessionLocalを取得します。
        初期化されていない場合は自動的に初期化します。
        """
        if self._session_local is None:
            self.initialize()
        return self._session_local

    @property
    def connection_string(self) -> str:
        """
        PostgreSQL接続文字列を取得します。
        初期化されていない場合は自動的に初期化します。
        """
        if self._connection_string is None:
            self.initialize()
        return self._connection_string

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        データベースセッションのコンテキストマネージャー。
        
        使用例:
            with db.get_session() as session:
                session.query(Model).all()
        """
        if self._session_local is None:
            self.initialize()
        
        db = self._session_local()
        try:
            yield db
        finally:
            db.close()

    def dispose(self):
        """
        データベース接続プールを破棄します。
        アプリケーション終了時などに使用します。
        """
        if self._engine:
            self._engine.dispose()
            NaviApiLog.info("PostgreSQL connection pool disposed")
