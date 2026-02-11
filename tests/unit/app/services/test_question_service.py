import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.requests.question_request import QuestionRequest
from app.repositories.manual_repository import ManualDto
from app.models.responses.question_response import QuestionResponse
from app.services.question_service import QuestionService


class TestQuestionService:
    """QuestionServiceのテストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッションを返すフィクスチャ"""
        return Mock()

    @pytest.mark.parametrize(
        "company_id, application_id, question_text, manuals, expected_file_paths",
        [
            (
                1,
                10,
                "この製品の使い方を教えてください",
                [
                    ManualDto(company_id=1, application_id=10, manual_id=100, file_extension="pdf"),
                    ManualDto(company_id=1, application_id=10, manual_id=101, file_extension="docx"),
                ],
                ["manuals/1/10/100.pdf", "manuals/1/10/101.docx"]
            ),
            (
                1,
                None,
                "全体的な概要を教えてください",
                [
                    ManualDto(company_id=1, application_id=10, manual_id=100, file_extension="pdf"),
                    ManualDto(company_id=1, application_id=10, manual_id=101, file_extension="docx"),
                    ManualDto(company_id=1, application_id=20, manual_id=200, file_extension="pdf"),
                ],
                ["manuals/1/10/100.pdf", "manuals/1/10/101.docx", "manuals/1/20/200.pdf"]
            ),
            (
                999,
                999,
                "何か質問",
                [],
                []
            ),
            (
                1,
                99,
                "テスト質問",
                [ManualDto(company_id=1, application_id=99, manual_id=888, file_extension="txt")],
                ["manuals/1/99/888.txt"]
            ),
            (
                2,
                50,
                "様々なファイル形式のマニュアルについて",
                [
                    ManualDto(company_id=2, application_id=50, manual_id=501, file_extension="pdf"),
                    ManualDto(company_id=2, application_id=50, manual_id=502, file_extension="docx"),
                    ManualDto(company_id=2, application_id=50, manual_id=503, file_extension="xlsx"),
                ],
                ["manuals/2/50/501.pdf", "manuals/2/50/502.docx", "manuals/2/50/503.xlsx"]
            ),
        ],
        ids=lambda x: x if isinstance(x, str) else ""
    )
    @patch('app.services.question_service.QuestionLLMHelper')
    @patch('app.services.question_service.ManualRepository.get_by_company_id')
    def test_answer_success(
        self,
        mock_get_manuals,
        mock_llm_helper_class,
        mock_session,
        company_id,
        application_id,
        question_text,
        manuals,
        expected_file_paths
    ):
        """answerメソッドの正常系テスト（パラメータ化）"""
        question_service = QuestionService()
        
        expected_answer = f"回答: {question_text}"
        
        question_request = QuestionRequest(
            application_id=application_id,
            question=question_text
        )

        mock_get_manuals.return_value = manuals

        mock_llm_helper_instance = MagicMock()
        mock_llm_helper_instance.answer_question.return_value = expected_answer
        mock_llm_helper_class.return_value = mock_llm_helper_instance

        # Act
        # @transactionデコレータをバイパスして直接メソッドを呼び出す
        # answer.__wrapped__を使用してデコレータをスキップ
        result = question_service.answer.__wrapped__(
            question_service,
            session=mock_session,
            question_request=question_request,
            company_id=company_id
        )

        # Assert
        mock_get_manuals.assert_called_once_with(
            session=mock_session,
            company_id=company_id,
            application_id=application_id
        )

        mock_llm_helper_class.assert_called_once_with(
            file_paths=expected_file_paths,
            collection_name="manuals"
        )

        mock_llm_helper_instance.answer_question.assert_called_once_with(
            question_text=question_text
        )

        assert result == QuestionResponse(answer=expected_answer)
