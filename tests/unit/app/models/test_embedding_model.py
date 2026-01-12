import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from app.models.llm.embedding_model import SentenceTransformerEmbeddingsModel


class TestSentenceTransformerEmbeddingsModel:
    """SentenceTransformerEmbeddingsModelのユニットテストクラス"""
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "CPU deviceで正常に初期化できる",
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu"
        },
        {
            "description": "CUDA deviceで正常に初期化できる",
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "device": "cuda"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_initialization_success(self, mock_sentence_transformer, test_case):
        """初期化成功テスト"""
        model_name = test_case["model_name"]
        device = test_case["device"]
        
        # モックの設定
        mock_model_instance = Mock()
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name=model_name,
            device=device
        )
        
        # 検証
        assert embedding_model is not None
        assert embedding_model.model == mock_model_instance
        mock_sentence_transformer.assert_called_once_with(model_name, device=device)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "model_nameが空文字列の場合、ValueErrorを発生させる",
            "model_name": "",
            "device": "cpu",
            "expected_error": ValueError,
            "error_message": "model_nameを空にすることはできません"
        },
        {
            "description": "model_nameがNoneの場合、ValueErrorを発生させる",
            "model_name": None,
            "device": "cpu",
            "expected_error": ValueError,
            "error_message": "model_nameを空にすることはできません"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_initialization_invalid_model_name(self, mock_sentence_transformer, test_case):
        """model_nameが無効な場合の初期化失敗テスト"""
        model_name = test_case["model_name"]
        device = test_case["device"]
        expected_error = test_case["expected_error"]
        error_message = test_case["error_message"]
        
        # テスト対象の実行と検証
        with pytest.raises(expected_error, match=error_message):
            SentenceTransformerEmbeddingsModel(model_name=model_name, device=device)
        
        # SentenceTransformerが呼ばれていないことを確認
        mock_sentence_transformer.assert_not_called()
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "モデルのロードに失敗した場合、Exceptionを発生させる",
            "model_name": "invalid-model-name",
            "device": "cpu",
            "exception_type": Exception,
            "exception_message": "埋め込みモデルのロードに失敗しました"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_initialization_model_load_failure(self, mock_sentence_transformer, test_case):
        """モデルのロード失敗時のテスト"""
        model_name = test_case["model_name"]
        device = test_case["device"]
        exception_type = test_case["exception_type"]
        exception_message = test_case["exception_message"]
        
        # モックの設定：例外を発生させる
        mock_sentence_transformer.side_effect = exception_type(exception_message)
        
        # テスト対象の実行と検証
        with pytest.raises(exception_type, match=exception_message):
            SentenceTransformerEmbeddingsModel(model_name=model_name, device=device)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "単一テキストを正常に埋め込みベクトルに変換できる",
            "text": "これはテストテキストです",
            "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        {
            "description": "英語テキストを正常に埋め込みベクトルに変換できる",
            "text": "This is a test text",
            "embedding_vector": [0.5, 0.4, 0.3, 0.2, 0.1]
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_query_success(self, mock_sentence_transformer, test_case):
        """embed_query成功テスト"""
        text = test_case["text"]
        embedding_vector = test_case["embedding_vector"]
        
        # モックの設定
        mock_model_instance = Mock()
        mock_numpy_array = np.array(embedding_vector)
        mock_model_instance.encode.return_value = mock_numpy_array
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        result = embedding_model.embed_query(text)
        
        # 検証
        assert result == embedding_vector
        mock_model_instance.encode.assert_called_once_with(text)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "空文字列の場合、ValueErrorを発生させる",
            "text": "",
            "expected_error": ValueError,
            "error_message": "textを空にすることはできません"
        },
        {
            "description": "Noneの場合、ValueErrorを発生させる",
            "text": None,
            "expected_error": ValueError,
            "error_message": "textを空にすることはできません"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_query_invalid_text(self, mock_sentence_transformer, test_case):
        """embed_queryの無効なテキストの場合の失敗テスト"""
        text = test_case["text"]
        expected_error = test_case["expected_error"]
        error_message = test_case["error_message"]
        
        # モックの設定
        mock_model_instance = Mock()
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        
        # 検証
        with pytest.raises(expected_error, match=error_message):
            embedding_model.embed_query(text)
        
        # encodeが呼ばれていないことを確認
        mock_model_instance.encode.assert_not_called()
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "埋め込み処理に失敗した場合、Exceptionを発生させる",
            "text": "test text",
            "exception_type": Exception,
            "exception_message": "テキストの埋め込み処理に失敗しました"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_query_encoding_failure(self, mock_sentence_transformer, test_case):
        """embed_queryのエンコーディング失敗時のテスト"""
        text = test_case["text"]
        exception_type = test_case["exception_type"]
        exception_message = test_case["exception_message"]
        
        # モックの設定：例外を発生させる
        mock_model_instance = Mock()
        mock_model_instance.encode.side_effect = exception_type(exception_message)
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        
        # 検証
        with pytest.raises(exception_type, match=exception_message):
            embedding_model.embed_query(text)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "複数のテキストを正常に埋め込みベクトルに変換できる",
            "texts": ["テキスト1", "テキスト2", "テキスト3"],
            "embedding_vectors": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9]
            ]
        },
        {
            "description": "単一のテキストリストも処理できる",
            "texts": ["単一テキスト"],
            "embedding_vectors": [[0.1, 0.2, 0.3]]
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_documents_success(self, mock_sentence_transformer, test_case):
        """embed_documents成功テスト"""
        texts = test_case["texts"]
        embedding_vectors = test_case["embedding_vectors"]
        
        # モックの設定
        mock_model_instance = Mock()
        
        def mock_encode(text):
            index = texts.index(text)
            return np.array(embedding_vectors[index])
        
        mock_model_instance.encode.side_effect = mock_encode
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        result = embedding_model.embed_documents(texts)
        
        # 検証
        assert result == embedding_vectors
        assert mock_model_instance.encode.call_count == len(texts)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "空のリストの場合、空のリストを返す",
            "texts": [],
            "expected_result": []
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_documents_empty_list(self, mock_sentence_transformer, test_case):
        """embed_documentsの空のリストの場合のテスト"""
        texts = test_case["texts"]
        expected_result = test_case["expected_result"]
        
        # モックの設定
        mock_model_instance = Mock()
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        result = embedding_model.embed_documents(texts)
        
        # 検証
        assert result == expected_result
        mock_model_instance.encode.assert_not_called()
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "空文字列を含むリストの場合、空文字列をスキップする",
            "texts": ["テキスト1", "", "テキスト2"],
            "valid_texts": ["テキスト1", "テキスト2"],
            "embedding_vectors": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6]
            ]
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_documents_skip_empty_strings(self, mock_sentence_transformer, test_case):
        """embed_documentsの空文字列をスキップするテスト"""
        texts = test_case["texts"]
        valid_texts = test_case["valid_texts"]
        embedding_vectors = test_case["embedding_vectors"]
        
        # モックの設定
        mock_model_instance = Mock()
        
        def mock_encode(text):
            index = valid_texts.index(text)
            return np.array(embedding_vectors[index])
        
        mock_model_instance.encode.side_effect = mock_encode
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        result = embedding_model.embed_documents(texts)
        
        # 検証
        assert result == embedding_vectors
        assert mock_model_instance.encode.call_count == len(valid_texts)
    
    @pytest.mark.parametrize("test_case", [
        {
            "description": "埋め込み処理に失敗した場合、Exceptionを発生させる",
            "texts": ["テキスト1", "テキスト2"],
            "exception_type": Exception,
            "exception_message": "ドキュメントの埋め込み処理に失敗しました"
        }
    ], ids=lambda x: x["description"])
    @patch('app.models.llm.embedding_model.SentenceTransformer')
    def test_embed_documents_encoding_failure(self, mock_sentence_transformer, test_case):
        """embed_documentsのエンコーディング失敗時のテスト"""
        texts = test_case["texts"]
        exception_type = test_case["exception_type"]
        exception_message = test_case["exception_message"]
        
        # モックの設定：例外を発生させる
        mock_model_instance = Mock()
        mock_model_instance.encode.side_effect = exception_type(exception_message)
        mock_sentence_transformer.return_value = mock_model_instance
        
        # テスト対象の実行
        embedding_model = SentenceTransformerEmbeddingsModel(
            model_name="test-model",
            device="cpu"
        )
        
        # 検証
        with pytest.raises(exception_type, match=exception_message):
            embedding_model.embed_documents(texts)
