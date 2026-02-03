import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.models.llm.question_llm_model import QuestionLLMModel, State
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from botocore.exceptions import ClientError


class TestQuestionLLMModel:
    """QuestionLLMModelのテストクラス"""
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "正常に初期化できる（file_pathsあり: 1件）",
            "file_paths": ["manual1.pdf"],
            "collection_name": "manuals",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": {
                "model_name": "gpt-3.5-turbo",
                "base_url": "http://localhost:8000",
                "api_key": "test-api-key",
                "temperature": 0.7
            },
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "question_llm_config": {
                "system_context": "あなたは親切なアシスタントです。",
                "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
            }
        },
        {
            "description": "正常に初期化できる（file_pathsあり）",
            "file_paths": ["manual1.pdf", "manual2.pdf"],
            "collection_name": "test_manuals",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": {
                "model_name": "gpt-4",
                "base_url": "http://localhost:8000",
                "api_key": "test-api-key",
                "temperature": 0.5
            },
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "question_llm_config": {
                "system_context": "You are a helpful assistant.",
                "prompt_context": "Question: {question}\nContext: {context}\nAnswer:"
            }
        }
    ], ids=lambda x: x["description"])
    def test_initialization_success(
        self,
        test_case,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """QuestionLLMModelの初期化成功テスト"""
        postgresql_config = test_case["postgresql_config"]
        llm_config = test_case["llm_config"]
        embedding_config = test_case["embedding_config"]
        question_llm_config = test_case["question_llm_config"]
        file_paths = test_case["file_paths"]
        collection_name = test_case.get("collection_name", setup_postgresql_test_collection)
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=file_paths,
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        # 検証
                        assert model is not None
                        assert model.llm is not None
                        assert model.vector_store is not None
                        assert model.retriever is not None
                        assert model.question_llm_setting == question_llm_config
                        assert model.file_paths == file_paths
                        assert model.collection_name == setup_postgresql_test_collection

    @pytest.mark.parametrize("test_case", [
        {
            "description": "question_llm_settingが設定されていない",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": {
                "model_name": "gpt-3.5-turbo",
                "base_url": "http://localhost:8000",
                "api_key": "test-api-key",
                "temperature": 0.7
            },
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "question_llm_config": None,
            "expected_error": RuntimeError,
            "error_match": "質問応答モデルの初期化に失敗しました"
        },
        {
            "description": "system_contextが欠けている",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": {
                "model_name": "gpt-3.5-turbo",
                "base_url": "http://localhost:8000",
                "api_key": "test-api-key",
                "temperature": 0.7
            },
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "question_llm_config": {
                "prompt_context": "質問: {question}\n回答:"
            },
            "expected_error": RuntimeError,
            "error_match": "質問応答モデルの初期化に失敗しました"
        },
        {
            "description": "prompt_contextが欠けている",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": {
                "model_name": "gpt-3.5-turbo",
                "base_url": "http://localhost:8000",
                "api_key": "test-api-key",
                "temperature": 0.7
            },
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "question_llm_config": {
                "system_context": "あなたは親切なアシスタントです。"
            },
            "expected_error": RuntimeError,
            "error_match": "質問応答モデルの初期化に失敗しました"
        }
    ], ids=lambda x: x["description"])
    def test_initialization_failure(
        self,
        test_case,
        setup_test_parameters,
        setup_postgresql_test_collection
    ):
        """QuestionLLMModelの初期化失敗テスト"""
        postgresql_config = test_case["postgresql_config"]
        llm_config = test_case["llm_config"]
        embedding_config = test_case["embedding_config"]
        question_llm_config = test_case.get("question_llm_config")
        expected_error = test_case["expected_error"]
        error_match = test_case["error_match"]
        
        # Noneの場合は自動的に削除、それ以外は設定される
        # question_llm_configがNoneの場合は削除するためFalseを渡す
        with setup_test_parameters(
            postgresql_config=postgresql_config,
            llm_config=llm_config,
            embedding_config=embedding_config,
            question_llm_config=False if question_llm_config is None else question_llm_config
        ):
            with pytest.raises(expected_error, match=error_match):
                QuestionLLMModel(
                    file_paths=["manual1.pdf"],
                    collection_name=setup_postgresql_test_collection
                )

    @pytest.mark.parametrize("test_case", [
        {
            "description": "初回メッセージ追加（SystemMessageとHumanMessageを追加）",
            "query": "こんにちは",
            "initial_messages": [],
            "system_context": "あなたは親切なアシスタントです。",
            "expected_message_count": 2,
            "expected_first_type": SystemMessage,
            "expected_second_type": HumanMessage
        },
        {
            "description": "2回目以降のメッセージ追加（HumanMessageのみ追加）",
            "query": "元気ですか？",
            "initial_messages": [
                SystemMessage(content="あなたは親切なアシスタントです。"),
                HumanMessage(content="こんにちは")
            ],
            "system_context": "あなたは親切なアシスタントです。",
            "expected_message_count": 1,
            "expected_first_type": HumanMessage
        },
        {
            "description": "空のクエリでもメッセージ追加",
            "query": "",
            "initial_messages": [],
            "system_context": "あなたは親切なアシスタントです。",
            "expected_message_count": 2,
            "expected_first_type": SystemMessage,
            "expected_second_type": HumanMessage
        }
    ], ids=lambda x: x["description"])
    def test_add_message(
        self,
        test_case,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """add_messageメソッドのテスト"""
        postgresql_config = {
            "user": "vector_user",
            "password": "vector_password",
            "host": "localhost",
            "port": "5432",
            "database": "vector_db"
        }
        llm_config = {
            "model_name": "gpt-3.5-turbo",
            "base_url": "http://localhost:8000",
            "api_key": "test-api-key",
            "temperature": 0.7
        }
        embedding_config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        }
        question_llm_config = {
            "system_context": test_case["system_context"],
            "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
        }
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=["manual1.pdf"],
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        state = State(
                            query=test_case["query"],
                            messages=test_case["initial_messages"]
                        )
                        
                        result = model.add_message(state)
                        
                        # 検証
                        assert "messages" in result
                        assert len(result["messages"]) == test_case["expected_message_count"]
                        assert isinstance(result["messages"][0], test_case["expected_first_type"])
                        
                        if test_case["expected_message_count"] == 2:
                            assert isinstance(result["messages"][1], test_case["expected_second_type"])
                            if test_case["query"]:
                                assert result["messages"][1].content == test_case["query"]

    @pytest.mark.parametrize("test_case", [
        {
            "description": "空のクエリ",
            "query": "",
            "mock_chain_output": None,
            "expected_answer": "質問が空です。質問を入力してください。"
        }
    ], ids=lambda x: x["description"])
    def test_llm_response(
        self,
        test_case,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """llm_responseメソッドのテスト"""
        postgresql_config = {
            "user": "vector_user",
            "password": "vector_password",
            "host": "localhost",
            "port": "5432",
            "database": "vector_db"
        }
        llm_config = {
            "model_name": "gpt-3.5-turbo",
            "base_url": "http://localhost:8000",
            "api_key": "test-api-key",
            "temperature": 0.7
        }
        embedding_config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        }
        question_llm_config = {
            "system_context": "あなたは親切なアシスタントです。",
            "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
        }
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=["manual1.pdf"],
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        state = State(
                            query=test_case["query"],
                            messages=[]
                        )
                        
                        result = model.llm_response(state)
                        
                        # 検証
                        assert "messages" in result
                        assert len(result["messages"]) == 1
                        assert isinstance(result["messages"][0], AIMessage)
                        assert test_case["expected_answer"] in result["messages"][0].content

    @pytest.mark.parametrize("test_case", [
        {
            "description": "正常なLLM応答",
            "query": "テストの質問です",
            "mock_chain_output": {
                "question": "テストの質問です",
                "context": ["コンテキスト1", "コンテキスト2"],
                "answer": "テストの回答です"
            },
            "expected_answer": "テストの回答です"
        },
        {
            "description": "空の回答",
            "query": "質問",
            "mock_chain_output": {
                "question": "質問",
                "context": [],
                "answer": ""
            },
            "expected_answer": "回答を生成できませんでした。別の質問をお試しください。"
        }
    ], ids=lambda x: x["description"])
    def test_llm_response_with_mock(
        self,
        test_case,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """llm_responseメソッドのモックを使ったテスト"""
        postgresql_config = {
            "user": "vector_user",
            "password": "vector_password",
            "host": "localhost",
            "port": "5432",
            "database": "vector_db"
        }
        llm_config = {
            "model_name": "gpt-3.5-turbo",
            "base_url": "http://localhost:8000",
            "api_key": "test-api-key",
            "temperature": 0.7
        }
        embedding_config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        }
        question_llm_config = {
            "system_context": "あなたは親切なアシスタントです。",
            "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
        }
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=["manual1.pdf"],
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        state = State(
                            query=test_case["query"],
                            messages=[]
                        )
                        
                        # chain全体をモック
                        with patch('app.models.llm.question_llm_model.RunnableParallel') as mock_parallel:
                            mock_chain = MagicMock()
                            mock_chain.invoke.return_value = test_case["mock_chain_output"]
                            mock_parallel.return_value.assign.return_value = mock_chain
                            
                            result = model.llm_response(state)
                        
                        # 検証
                        assert "messages" in result
                        assert len(result["messages"]) == 1
                        assert isinstance(result["messages"][0], AIMessage)
                        assert test_case["expected_answer"] in result["messages"][0].content

    def test_llm_response_exception_handling(
        self,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """llm_responseメソッドの例外処理テスト"""
        postgresql_config = {
            "user": "vector_user",
            "password": "vector_password",
            "host": "localhost",
            "port": "5432",
            "database": "vector_db"
        }
        llm_config = {
            "model_name": "gpt-3.5-turbo",
            "base_url": "http://localhost:8000",
            "api_key": "test-api-key",
            "temperature": 0.7
        }
        embedding_config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        }
        question_llm_config = {
            "system_context": "あなたは親切なアシスタントです。",
            "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
        }
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=["manual1.pdf"],
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        state = State(
                            query="テストクエリ",
                            messages=[]
                        )
                        
                        # チェーン全体をモックして例外を投げるようにする
                        with patch('app.models.llm.question_llm_model.RunnableParallel') as mock_parallel:
                            mock_chain = MagicMock()
                            mock_chain.invoke.side_effect = Exception("LLMエラー")
                            mock_parallel.return_value.assign.return_value = mock_chain
                            
                            # 例外が発生することを確認
                            with pytest.raises(RuntimeError) as exc_info:
                                model.llm_response(state)
                            
                            # 例外メッセージを確認
                            assert str(exc_info.value) == "回答の生成中にエラーが発生しました"

    def test_get_graph(
        self,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """get_graphメソッドのテスト"""
        postgresql_config = {
            "user": "vector_user",
            "password": "vector_password",
            "host": "localhost",
            "port": "5432",
            "database": "vector_db"
        }
        llm_config = {
            "model_name": "gpt-3.5-turbo",
            "base_url": "http://localhost:8000",
            "api_key": "test-api-key",
            "temperature": 0.7
        }
        embedding_config = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        }
        question_llm_config = {
            "system_context": "あなたは親切なアシスタントです。",
            "prompt_context": "質問: {question}\nコンテキスト: {context}\n回答:"
        }
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_parameter("question_llm_setting", json.dumps(question_llm_config)):
                        model = QuestionLLMModel(
                            file_paths=["manual1.pdf"],
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        graph = model.get_graph()
                        
                        # 検証
                        assert graph is not None
                        from langgraph.graph.state import CompiledStateGraph
                        assert isinstance(graph, CompiledStateGraph)

    def test_state_model(self):
        """Stateモデルのテスト"""
        # 正常なState作成
        state = State(query="テスト質問", messages=[])
        assert state.query == "テスト質問"
        assert state.messages == []
        
        # メッセージありのState作成
        messages = [
            SystemMessage(content="システム"),
            HumanMessage(content="人間")
        ]
        state = State(query="質問", messages=messages)
        assert state.query == "質問"
        assert len(state.messages) == 2
        assert isinstance(state.messages[0], SystemMessage)
        assert isinstance(state.messages[1], HumanMessage)
