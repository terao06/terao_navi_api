from fastapi import FastAPI
from app.api.endpoints.question import question_router
from app.api.endpoints.auth_token import token_router
from app.core.logging import NaviApiLog

# ロギング初期設定
NaviApiLog.setup(
    log_level='INFO',
    enable_file_logging=False  # 必要に応じてTrueに変更
)

app = FastAPI()

app.include_router(token_router)
app.include_router(question_router)
