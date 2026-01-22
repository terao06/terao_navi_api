from app.models.llm.question_llm_model import QuestionLLMModel, State
from typing import Optional


class QuestionLLMHelper:
    def __init__(self, file_paths: Optional[list[str]] = None, collection_name: str = "manuals"):
        """
        質問応答ヘルパーを初期化する
        
        Args:
            file_paths: フィルタリングするファイルパスのリスト
            collection_name: 使用するコレクション名
        """
        self.question_llm_model = QuestionLLMModel(file_paths=file_paths, collection_name=collection_name)

    def answer_question(self, question_text: str) -> str:
        """
        質問に対する回答を生成する
        
        Args:
            question_text: 質問テキスト
            
        Returns:
            str: 生成された回答テキスト
        """
        graph = self.question_llm_model.get_graph()
        user_query = State(query=question_text)
        first_response = graph.invoke(input=user_query)
        return first_response.get("messages")[-1].content
