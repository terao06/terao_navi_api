from fastapi import APIRouter
from fastapi import Depends
from app.models.requests.question_request import QuestionRequest
from app.api.depend import require_api_key
from app.models.dynamodb.auth_client_model import AuthClientModel
from app.services.question_service import QuestionService
from app.middlewares.request_wrapper import request_rapper
from app.middlewares.response_wrapper import response_rapper


question_router = APIRouter()

@question_router.post("/ask")
@response_rapper()
@request_rapper()
def read_root(
    request: QuestionRequest,
    client: AuthClientModel = Depends(require_api_key)):
    """
    質問に対する回答を生成します。
    
    response_wrapper()デコレーターによって、
    レスポンスは自動的に {"status": "success", "data": {...}} の形式にラップされます。
    """
    return QuestionService().answer(
        question_request=request,
        company_id=client.company_id
    )
