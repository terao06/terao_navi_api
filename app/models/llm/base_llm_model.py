from abc import abstractmethod
import os
from app.core.aws.ssm_client import SsmClient
from app.core.database.postgresql import PostgreSQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders.s3_file import S3FileLoader
from langchain_postgres import PGVector
from langgraph.graph.state import CompiledStateGraph
from app.models.llm.embedding_model import EmbeddingModelManager
from sqlalchemy import text
from app.core.logging import NaviApiLog


USE_OPEN_AI = False

class BaseLLMModel:
    def __init__(self, file_paths: list[str], collection_name: str = "manuals") -> None:
        if not file_paths:
            raise ValueError("file_pathsを空にすることはできません")

        self.params = SsmClient()
        self.pg_database = PostgreSQLDatabase()

        self.collection_name = collection_name  # コレクション名を保存
        self.file_paths = file_paths  # フィルタ用のファイルパスを保存

        llm_setting = self.params.get_parameter("llm_setting")
        embedding_setting = self.params.get_parameter("embedding_setting")

        try:
            embeddings = EmbeddingModelManager.get_embedding_model(
                model_name=embedding_setting.get("model_name"),
                api_key=embedding_setting.get("api_key"),
                device=embedding_setting.get("device", "cpu"),
                use_api=USE_OPEN_AI)
            
            self.llm = ChatOpenAI(
                model=llm_setting.get("model_name"),
                base_url=llm_setting.get("base_url", None),
                api_key=llm_setting.get("api_key"),
                temperature=llm_setting.get("temperature"),
            )
        except Exception as e:
            NaviApiLog.error(f"LLM/Embeddingモデルの初期化に失敗しました: {e}")
            raise RuntimeError("言語モデルの初期化に失敗しました")

        self.llm = ChatOpenAI(
            model=llm_setting.get("model_name"),
            base_url=llm_setting.get("base_url", None),
            api_key=llm_setting.get("api_key"),
            temperature=llm_setting.get("temperature"),
        )

        self.region_name = os.getenv("AWS_REGION", "ap-northeast-1")
        self.endpoint_url = os.getenv("S3_ENDPOINT")

        try:
            self.vector_store = PGVector(
                embeddings=embeddings,
                collection_name=collection_name,
                connection=self.pg_database.connection_string,
                use_jsonb=True,
                pre_delete_collection=False,
            )
            # 初期化時にデフォルトのretrieverを設定
            self.retriever = self._create_retriever()

        except Exception as e:
            NaviApiLog.error(f"Vector Storeの初期化に失敗しました: {e}")
            raise RuntimeError("ベクターストアの初期化に失敗しました")

    def _create_retriever(self):
        """
        指定されたfile_pathsでフィルタリングされたretrieverを作成する。
        file_pathsがNoneの場合、フィルタなしのretrieverを返す。
        """
        try:
            search_kwargs = {}
            search_kwargs["filter"] = {"source": {"$in": self.file_paths}}
            
            return self.vector_store.as_retriever(search_kwargs=search_kwargs)
        except Exception as e:
            NaviApiLog.error(f"Retrieverの作成に失敗しました: {e}")
            raise RuntimeError("検索機能の作成に失敗しました")

    def get_existing_sources(self) -> set[str]:
        """
        Vector DBに既に登録されているsourceのセットを取得する。
        重複チェック用に呼び出し側で使用する。
        
        Returns:
            set[str]: 既存のsourceパスのセット
            
        Raises:
            Exception: データベース接続またはクエリ実行に失敗した場合
        """
        try:
            with self.pg_database.engine.connect() as conn:
                # collection_nameに対応するcollection_idを取得
                collection_query = text(
                    "SELECT uuid FROM langchain_pg_collection WHERE name = :collection_name"
                )
                collection_result = conn.execute(
                    collection_query, 
                    {"collection_name": self.collection_name}
                )
                collection_row = collection_result.fetchone()
                
                if not collection_row:
                    NaviApiLog.info(f"コレクション '{self.collection_name}' が見つかりません。既存のドキュメントはありません。")
                    return set()
                
                collection_id = collection_row[0]
                
                # 該当コレクションの全てのsourceを取得
                source_query = text(
                    "SELECT DISTINCT cmetadata->>'source' as source "
                    "FROM langchain_pg_embedding "
                    "WHERE collection_id = :collection_id"
                )
                source_result = conn.execute(source_query, {"collection_id": collection_id})
                
                existing_sources = {row[0] for row in source_result if row[0]}
                NaviApiLog.info(f"コレクション '{self.collection_name}' に {len(existing_sources)} 件の既存ソースが見つかりました")
                return existing_sources
                
        except Exception as e:
            NaviApiLog.error(f"既存ソースの取得に失敗しました: {e}")
            raise RuntimeError("データの取得に失敗しました")

    def ingest_documents(self, bucket_name: str) -> None:
        """
        指定されたファイルをS3からロードしてVector DBに追加する。
        初期化バッチ等から呼び出すことを想定。
        重複チェックは呼び出し側で行うこと。
        
        Args:
            bucket_name: S3バケット名
            file_paths: インジェストするファイルパスのリスト
            
        Raises:
            ValueError: bucket_nameまたはfile_pathsが無効な場合
            Exception: ドキュメントのロードまたは追加に失敗した場合
        """
        if not bucket_name:
            raise ValueError("bucket_nameを空にすることはできません")
        
        try:
            documents = self._load_documents(bucket_name)
            if documents:
                NaviApiLog.info(f"{len(documents)} 件のドキュメントをベクターストアに追加します")
                self.vector_store.add_documents(documents)
                NaviApiLog.info(f"{len(documents)} 件のドキュメントをベクターストアに正常に追加しました")
            else:
                NaviApiLog.warning("インジェストするドキュメントがロードされませんでした")
        except Exception as e:
            NaviApiLog.error(f"ドキュメントのインジェストに失敗しました: {e}")
            raise RuntimeError("ドキュメントの追加に失敗しました")

    def _load_documents(self, bucket_name: str) -> list:
        """
        S3からドキュメントをロード
        
        Args:
            bucket_name: S3バケット名
            file_paths: ロードするファイルパスのリスト
            
        Returns:
            list: ロードされたドキュメントのリスト
        """
        documents = []
        failed_files = []
        
        # AWS認証情報の検証
        endpoint_url = os.getenv("S3_ENDPOINT")
        access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not access_key_id or not secret_access_key:
            NaviApiLog.warning("AWS認証情報が環境変数に見つかりません")
        
        for file_path in self.file_paths:
            try:
                if not file_path:
                    NaviApiLog.warning("空のファイルパスが検出されました。スキップします")
                    continue
                    
                loader = S3FileLoader(
                    bucket=bucket_name,
                    key=file_path,
                    endpoint_url=endpoint_url,
                    aws_access_key_id=access_key_id, 
                    aws_secret_access_key=secret_access_key,
                )
                loaded_docs = loader.load()
                
                if not loaded_docs:
                    NaviApiLog.warning(f"S3ファイルからドキュメントがロードされませんでした: {file_path}")
                    continue

                for doc in loaded_docs:
                    doc.metadata['source'] = f"{bucket_name}/{file_path}"
                documents.extend(loaded_docs)
                NaviApiLog.debug(f"{file_path} から {len(loaded_docs)} 件のドキュメントを正常にロードしました")
            except Exception as e:
                NaviApiLog.error(f"S3ファイル({file_path})のロードに失敗しました: {e}")
                failed_files.append(file_path)
        
        if failed_files:
            NaviApiLog.warning(f"{len(failed_files)} 件のファイルのロードに失敗しました: {failed_files}")

        return documents

    @abstractmethod
    def get_graph(self) -> CompiledStateGraph:
        raise NotImplementedError("get_graph関数が定義されていません。")
