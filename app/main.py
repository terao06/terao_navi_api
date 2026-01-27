from fastapi import FastAPI
from app.api.endpoints.question import question_router
from app.api.endpoints.auth_token import token_router
from app.core.logging import NaviApiLog
from fastapi.middleware.cors import CORSMiddleware

# ロギング初期設定
NaviApiLog.setup(
    log_level='INFO',
    enable_file_logging=False  # 必要に応じてTrueに変更
)

app = FastAPI()

origins = [
    "http://localhost:3000", # 例えばローカル開発
    # 他の必要なオリジンもここに追加
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 許可するオリジンのリスト
    allow_credentials=True,       # Cookie等の資格情報も許可する場合に設定
    allow_methods=["GET", "POST", "PUT", "DELETE"],     # 許可するHTTPメソッド（"GET", "POST" など）; "*" は全てを許可
    allow_headers=["*"],          # 許可するHTTPヘッダー; "*" は全てを許可
)

app.include_router(token_router)
app.include_router(question_router)
