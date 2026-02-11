import pytest
import json
from app.models.llm.base_llm_model import BaseLLMModel
from langgraph.graph import StateGraph
from typing import TypedDict


class ConcreteLLMModel(BaseLLMModel):
    """テスト用のBaseLLMModelの具象クラス"""
    def get_graph(self):
        # テスト用の簡易的な実装
        
        class State(TypedDict):
            messages: list
        
        workflow = StateGraph(State)
        workflow.set_entry_point("start")
        workflow.add_node("start", lambda x: x)
        workflow.set_finish_point("start")
        return workflow.compile()


class TestBaseLLMModel:
    """BaseLLMModelの統合テストクラス"""
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "正常に初期化できる",
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
        """BaseLLMModelの初期化成功テスト"""
        postgresql_config = test_case["postgresql_config"]
        llm_config = test_case["llm_config"]
        embedding_config = test_case["embedding_config"]
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    model = ConcreteLLMModel(
                        file_paths=["dummy.txt"],
                        collection_name=setup_postgresql_test_collection
                    )
                    # 検証
                    assert model is not None
                    assert model.llm is not None
                    assert model.vector_store is not None
                    assert model.retriever is not None
                    assert model.collection_name == setup_postgresql_test_collection
                    assert model.file_paths == ["dummy.txt"]
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "PostgreSQL設定が欠けている",
            "postgresql_config": None,
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
            "expected_error": Exception,
            "error_match": None
        },
        {
            "description": "LLM設定が欠けている",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password",
                "host": "localhost",
                "port": "5432",
                "database": "vector_db"
            },
            "llm_config": None,
            "embedding_config": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu"
            },
            "expected_error": Exception,
            "error_match": None
        },
        {
            "description": "Embedding設定が欠けている",
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
            "embedding_config": None,
            "expected_error": Exception,
            "error_match": None
        },
        {
            "description": "PostgreSQL設定が不完全",
            "postgresql_config": {
                "user": "vector_user",
                "password": "vector_password"
                # host, port, databaseが欠けている
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
            "expected_error": RuntimeError,
            "error_match": "ベクターストアの初期化に失敗しました"
        }
    ], ids=lambda x: x["description"])
    def test_initialization_failure(
        self,
        test_case,
        setup_test_parameters
    ):
        """BaseLLMModelの初期化失敗テスト"""
        postgresql_config = test_case["postgresql_config"]
        llm_config = test_case["llm_config"]
        embedding_config = test_case["embedding_config"]
        expected_error = test_case["expected_error"]
        error_match = test_case["error_match"]
        
        # Noneの場合は自動的に削除、それ以外は設定される
        with setup_test_parameters(
            postgresql_config=postgresql_config,
            llm_config=llm_config,
            embedding_config=embedding_config
        ):
            if error_match:
                with pytest.raises(expected_error, match=error_match):
                    ConcreteLLMModel(file_paths=["dummy.txt"], collection_name="test_collection")
            else:
                with pytest.raises(expected_error):
                    ConcreteLLMModel(file_paths=["dummy.txt"], collection_name="test_collection")
    
    def test_get_existing_sources_empty(
        self,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """空のコレクションから既存ソースを取得するテスト"""
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
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    model = ConcreteLLMModel(
                        file_paths=["dummy.txt"],
                        collection_name=setup_postgresql_test_collection
                    )
                    
                    # 既存ソースを取得
                    existing_sources = model.get_existing_sources()
                    
                    # 検証: 空のコレクション
                    assert isinstance(existing_sources, set)
                    assert len(existing_sources) == 0
    
    def test_get_existing_sources_with_documents(
        self,
        managed_secret,
        managed_parameter,
        managed_s3_bucket,
        setup_postgresql_test_collection
    ):
        """ドキュメント追加後に既存ソースを取得するテスト"""
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
        
        test_files = {
            "test_doc1.txt": "This is a test document for vector database.",
            "test_doc2.txt": "Another test document with different content."
        }
        bucket_name = "test-bucket-llm"
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_s3_bucket(bucket_name, test_files):
                        model = ConcreteLLMModel(
                            file_paths=list(test_files.keys()),
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        # ドキュメントをインジェスト
                        file_paths = list(test_files.keys())
                        model.ingest_documents(bucket_name)
                        
                        # 既存ソースを取得
                        existing_sources = model.get_existing_sources()
                        
                        # 検証
                        assert isinstance(existing_sources, set)
                        assert len(existing_sources) == 2
                        
                        expected_sources = {f"{bucket_name}/{fp}" for fp in file_paths}
                        assert existing_sources == expected_sources
    
    def test_ingest_documents_success(
        self,
        managed_secret,
        managed_parameter,
        managed_s3_bucket,
        setup_postgresql_test_collection
    ):
        """ドキュメントの正常なインジェストテスト"""
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
        
        test_files = {
            "test_doc1.txt": "This is a test document for vector database.",
            "test_doc2.txt": "Another test document with different content."
        }
        bucket_name = "test-bucket-llm"
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    with managed_s3_bucket(bucket_name, test_files):
                        model = ConcreteLLMModel(
                            file_paths=list(test_files.keys()),
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        # ドキュメントをインジェスト
                        file_paths = list(test_files.keys())
                        model.ingest_documents(bucket_name)
                        
                        # 検証: 既存ソースに追加されたファイルが含まれている
                        existing_sources = model.get_existing_sources()
                        assert len(existing_sources) > 0
                        
                        # sourceフィールドはbucket_name/file_path形式になっている
                        expected_sources = {f"{bucket_name}/{fp}" for fp in file_paths}
                        assert existing_sources == expected_sources
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "空のバケット名でエラー",
            "bucket_name": "",
            "file_paths": ["test.txt"],
            "expected_error": ValueError,
            "error_match": "bucket_nameを空にすることはできません"
        },
        {
            "description": "空のfile_pathsでエラー",
            "bucket_name": "test-bucket",
            "file_paths": [],
            "expected_error": ValueError,
            "error_match": "file_pathsを空にすることはできません"
        }
    ], ids=lambda x: x["description"])
    def test_ingest_documents_failure(
        self,
        test_case,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """ドキュメントのインジェスト失敗テスト"""
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
        
        bucket_name = test_case["bucket_name"]
        file_paths = test_case["file_paths"]
        expected_error = test_case["expected_error"]
        error_match = test_case["error_match"]
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    if not file_paths:
                        with pytest.raises(expected_error, match=error_match):
                            ConcreteLLMModel(
                                file_paths=file_paths,
                                collection_name=setup_postgresql_test_collection
                            )
                    else:
                        model = ConcreteLLMModel(
                            file_paths=file_paths,
                            collection_name=setup_postgresql_test_collection
                        )
                        
                        # エラーケース
                        with pytest.raises(expected_error, match=error_match):
                            model.ingest_documents(bucket_name)
    
    def test_get_graph_implementation(
        self,
        managed_secret,
        managed_parameter,
        setup_postgresql_test_collection
    ):
        """get_graphメソッドが実装されていることを確認"""
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
        
        with managed_secret("postgresql_setting", json.dumps(postgresql_config)):
            with managed_parameter("llm_setting", json.dumps(llm_config)):
                with managed_parameter("embedding_setting", json.dumps(embedding_config)):
                    model = ConcreteLLMModel(
                        file_paths=["dummy.txt"],
                        collection_name=setup_postgresql_test_collection
                    )
                    
                    # get_graphを呼び出し
                    graph = model.get_graph()
                    
                    # 検証
                    assert graph is not None
