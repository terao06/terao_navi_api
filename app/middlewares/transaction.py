from functools import wraps, lru_cache
import logging
from app.core.database.mysql import MySQLDatabase

logger = logging.getLogger(__name__)


@lru_cache()
def get_db():
    """
    Databaseインスタンスをキャッシュして返す
    """
    return MySQLDatabase()


def transaction(func):
    """
    トランザクションを開始し、コミットまたはロールバックを自動で行うデコレーター
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # キャッシュされたdbインスタンスを使用
        with get_db().get_session() as session:
            try:
                kwargs['session'] = session
                result = func(*args, **kwargs)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                logger.error(f"Error during transaction: {e}")
                raise
    return wrapper
