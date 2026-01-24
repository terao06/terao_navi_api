import pytest
from unittest.mock import patch, MagicMock
from app.helpers.question_llm_helper import QuestionLLMHelper
from app.models.llm.question_llm_model import State
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class TestQuestionLLMHelper:
    """QuestionLLMHelperのテストクラス"""

    DEFAULT_NOT_FOUND_MESSAGE = "申し訳ございません。\n回答が見つかりませんでした。"
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "正常に初期化できる（file_pathsなし）",
            "file_paths": None,
            "collection_name": "manuals"
        },
        {
            "description": "正常に初期化できる（file_pathsあり）",
            "file_paths": ["manual1.pdf", "manual2.pdf"],
            "collection_name": "test_manuals"
        },
        {
            "description": "正常に初期化できる（デフォルトcollection_name）",
            "file_paths": ["manual.pdf"],
            "collection_name": None  # デフォルト値を使用
        }
    ], ids=lambda x: x["description"])
    def test_initialization_success(self, test_case):
        """QuestionLLMHelperの初期化成功テスト（モック使用）"""
        file_paths = test_case["file_paths"]
        collection_name = test_case["collection_name"]
        
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_instance = MagicMock()
            mock_model_class.return_value = mock_instance
            
            if collection_name is None:
                helper = QuestionLLMHelper(file_paths=file_paths)
                # デフォルト値"manuals"で呼ばれることを確認
                mock_model_class.assert_called_once_with(
                    file_paths=file_paths,
                    collection_name="manuals"
                )
            else:
                helper = QuestionLLMHelper(
                    file_paths=file_paths,
                    collection_name=collection_name
                )
                # 指定した値で呼ばれることを確認
                mock_model_class.assert_called_once_with(
                    file_paths=file_paths,
                    collection_name=collection_name
                )
            
            # 検証
            assert helper is not None
            assert helper.question_llm_model == mock_instance

    @pytest.mark.parametrize("test_case", [
        {
            "description": "正常な質問応答",
            "question_text": "これは何ですか？",
            "mock_messages": [
                SystemMessage(content="あなたは親切なアシスタントです。"),
                HumanMessage(content="これは何ですか？"),
                AIMessage(content="これはテストの回答です。")
            ],
            "expected_answer": "これはテストの回答です。"
        },
        {
            "description": "複数のメッセージがある場合",
            "question_text": "教えてください",
            "mock_messages": [
                SystemMessage(content="システム"),
                HumanMessage(content="質問1"),
                AIMessage(content="回答1"),
                HumanMessage(content="教えてください"),
                AIMessage(content="詳細な回答です。")
            ],
            "expected_answer": "詳細な回答です。"
        },
        {
            "description": "短い質問",
            "question_text": "何？",
            "mock_messages": [
                SystemMessage(content="システム"),
                HumanMessage(content="何？"),
                AIMessage(content="簡単な回答")
            ],
            "expected_answer": "簡単な回答"
        }
    ], ids=lambda x: x["description"])
    def test_answer_question_success(self, test_case):
        """answer_questionメソッドの成功テスト（モック使用）"""
        question_text = test_case["question_text"]
        mock_messages = test_case["mock_messages"]
        expected_answer = test_case["expected_answer"]
        
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            # QuestionLLMModelのモックインスタンスを設定
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            # get_graphのモック
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            
            # graph.invokeの戻り値をモック
            mock_response = {"messages": mock_messages}
            mock_graph.invoke.return_value = mock_response
            
            # テスト実行（file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す）
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            result = helper.answer_question(question_text)
            
            # 検証
            assert result == expected_answer
            mock_model_instance.get_graph.assert_called_once()
            mock_graph.invoke.assert_called_once()
            
            # invokeに渡されたStateを確認
            call_args = mock_graph.invoke.call_args
            assert call_args is not None
            state_arg = call_args.kwargs.get('input')
            assert isinstance(state_arg, State)
            assert state_arg.query == question_text

    @pytest.mark.parametrize("test_case", [
        {
            "description": "空の質問テキスト",
            "question_text": "",
            "mock_messages": [
                SystemMessage(content="システム"),
                HumanMessage(content=""),
                AIMessage(content="質問が空です。")
            ],
            "expected_answer": "質問が空です。"
        },
        {
            "description": "長い質問テキスト",
            "question_text": "これは非常に長い質問テキストです。" * 10,
            "mock_messages": [
                SystemMessage(content="システム"),
                HumanMessage(content="これは非常に長い質問テキストです。" * 10),
                AIMessage(content="長い質問への回答")
            ],
            "expected_answer": "長い質問への回答"
        }
    ], ids=lambda x: x["description"])
    def test_answer_question_edge_cases(self, test_case):
        """answer_questionメソッドのエッジケーステスト（モック使用）"""
        question_text = test_case["question_text"]
        mock_messages = test_case["mock_messages"]
        expected_answer = test_case["expected_answer"]
        
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            mock_graph.invoke.return_value = {"messages": mock_messages}
            
            # file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            result = helper.answer_question(question_text)
            
            assert result == expected_answer

    def test_answer_question_with_file_paths(self):
        """file_pathsを指定した場合のテスト（モック使用）"""
        file_paths = ["manual1.pdf", "manual2.pdf"]
        question_text = "マニュアルの内容は？"
        
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            
            mock_messages = [
                SystemMessage(content="システム"),
                HumanMessage(content=question_text),
                AIMessage(content="マニュアルの内容についての回答")
            ]
            mock_graph.invoke.return_value = {"messages": mock_messages}
            
            helper = QuestionLLMHelper(
                file_paths=file_paths,
                collection_name="test_collection"
            )
            result = helper.answer_question(question_text)
            
            # 検証
            assert result == "マニュアルの内容についての回答"
            mock_model_class.assert_called_once_with(
                file_paths=file_paths,
                collection_name="test_collection"
            )

    def test_answer_question_model_exception(self):
        """QuestionLLMModelが例外を投げた場合のテスト"""
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            # get_graphが例外を投げる
            mock_model_instance.get_graph.side_effect = Exception("モデルエラー")
            
            # file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            
            with pytest.raises(Exception, match="モデルエラー"):
                helper.answer_question("テスト質問")

    def test_answer_question_graph_invoke_exception(self):
        """graph.invokeが例外を投げた場合のテスト"""
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            
            # graph.invokeが例外を投げる
            mock_graph.invoke.side_effect = Exception("グラフ実行エラー")
            
            # file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            
            with pytest.raises(Exception, match="グラフ実行エラー"):
                helper.answer_question("テスト質問")

    def test_answer_question_empty_messages(self):
        """messagesが空の場合のテスト"""
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            
            # 空のmessagesを返す
            mock_graph.invoke.return_value = {"messages": []}
            
            # file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            
            # messagesが空の場合、IndexErrorが発生するはず
            with pytest.raises(IndexError):
                helper.answer_question("テスト質問")

    def test_multiple_questions(self):
        """複数の質問を連続で実行するテスト"""
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance
            
            mock_graph = MagicMock()
            mock_model_instance.get_graph.return_value = mock_graph
            
            # 複数の質問に対する応答を設定
            responses = [
                {"messages": [AIMessage(content="回答1")]},
                {"messages": [AIMessage(content="回答2")]},
                {"messages": [AIMessage(content="回答3")]}
            ]
            mock_graph.invoke.side_effect = responses
            
            # file_pathsが空だと早期returnするため、ダミーのfile_pathsを渡す
            helper = QuestionLLMHelper(file_paths=["manual.pdf"])
            
            # 3つの質問を実行
            result1 = helper.answer_question("質問1")
            result2 = helper.answer_question("質問2")
            result3 = helper.answer_question("質問3")
            
            # 検証
            assert result1 == "回答1"
            assert result2 == "回答2"
            assert result3 == "回答3"
            assert mock_graph.invoke.call_count == 3
            # get_graphは初回のみ呼ばれる（キャッシュされる）
            assert mock_model_instance.get_graph.call_count == 3

    def test_answer_question_without_file_paths_returns_default_message(self):
        """file_paths未指定（または空）だと固定のメッセージを返すテスト"""
        with patch('app.helpers.question_llm_helper.QuestionLLMModel') as mock_model_class:
            mock_model_instance = MagicMock()
            mock_model_class.return_value = mock_model_instance

            helper = QuestionLLMHelper(file_paths=None)
            result = helper.answer_question("テスト質問")

            assert result == self.DEFAULT_NOT_FOUND_MESSAGE
            mock_model_instance.get_graph.assert_not_called()
