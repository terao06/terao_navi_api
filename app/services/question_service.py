from app.repositories.manual_repository import ManualRepository
from app.middlewares.transaction import transaction
from app.models.requests.question_request import QuestionRequest
from app.models.responses.question_response import QuestionResponse
from app.helpers.question_llm_helper import QuestionLLMHelper
from sqlalchemy.orm import Session
from app.core.logging import NaviApiLog

COMMON_PATH = "manuals"


class QuestionService:
    @transaction
    def answer(
        self,
        session: Session,
        question_request: QuestionRequest,
        company_id: int) -> QuestionResponse:
        NaviApiLog.info(
            f"マニュアルを取得します。"
            f"company_id={company_id} "
            f"application_id={question_request.application_id}"
        )
        manuals = ManualRepository.get_by_company_id(
            session=session,
            company_id=company_id,
            application_id=question_request.application_id
        )
        NaviApiLog.info(
            f"マニュアルを取得しました。"
            f"company_id={company_id} "
            f"application_id={question_request.application_id} "
            f"マニュアル数={len(manuals)}"
        )

        file_paths = []
        for manual in manuals:
            file_paths.append(
                f"{COMMON_PATH}/{manual.company_id}/{manual.application_id}/{manual.manual_id}.{manual.file_extension}"
            )
        NaviApiLog.info(f"s3ファイルパスリスト={file_paths}")

        answer = QuestionLLMHelper(
            file_paths=file_paths,collection_name=COMMON_PATH
        ).answer_question(question_text=question_request.question)

        return QuestionResponse(
            answer=answer
        )
