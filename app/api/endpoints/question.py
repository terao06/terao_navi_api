from fastapi import APIRouter
from fastapi import Depends
from app.models.requests.question_request import QuestionRequest
from app.api.depend import authenticate_access_token
from app.core.utils.token_util import TokenUtil
from app.services.question_service import QuestionService
from app.middlewares.request_wrapper import request_rapper
from app.middlewares.response_wrapper import response_rapper


question_router = APIRouter()

@question_router.post("/ask")
@response_rapper()
@request_rapper()
def read_root(
    request: QuestionRequest,
    company_id: int = Depends(authenticate_access_token)):
    """
    質問に対する回答を生成します。
    
    response_wrapper()デコレーターによって、
    レスポンスは自動的に {"status": "success", "data": {...}} の形式にラップされます。
    """

    return QuestionService().answer(
        question_request=request,
        company_id=company_id,
    )
