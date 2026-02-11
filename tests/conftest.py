import pytest
import os
import contextlib
import boto3
from botocore.exceptions import ClientError

# テスト実行用の環境変数を初期設定（インポート時の動作保証用）
os.environ["AWS_REGION"] = "ap-northeast-1"
os.environ["SECRETS_MANAGER_ENDPOINT"] = "http://127.0.0.1:4566"
os.environ["SSM_ENDPOINT"] = "http://127.0.0.1:4566"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["S3_ENDPOINT"] = "http://127.0.0.1:4566"

from app.core.database.mysql import MySQLDatabase
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

# すべてのモデルをインポートしてSQLAlchemyのBaseに登録
from app.models.mysql.company_model import CompanyModel
from app.models.mysql.application_model import ApplicationModel
from app.models.mysql.manual_model import ManualModel
from app.models.mysql.user_model import UserModel
from app.models.mysql.role_model import RoleModel


@pytest.fixture(scope="function")
def session(setup_env_vars):
    """
    テスト用のデータベースセッションを提供します。
    setup_env_vars に依存して、テスト用のMySQL設定が確実に登録された後に実行されます。
    """
    db = MySQLDatabase()
    connection = db.engine.connect()
    transaction = connection.begin()

    session = db.session_local(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def insert_test_data(session: Session):
    def _insert(sql_filenames: list[str]):
        base_path = os.path.dirname(__file__)
        for filename in sql_filenames:
            file_path = os.path.join(base_path, 'test_data', 'mysql', filename)
            # check if file exists to avoid error if extra files listed
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                    
                    for statement in statements:
                        session.execute(text(statement))
        session.flush()

    return _insert

@pytest.fixture(scope="function", autouse=True)
def auto_insert_default_data(request: pytest.FixtureRequest):
    """DBを使うテストにだけ、基本となるテストデータを投入します。

    以前は autouse fixture が常に `insert_test_data` -> `session` を解決してしまい、
    DB不要のテスト（例: SSM/Secrets など）でもMySQL接続が発生していました。
    """
    # このテストでDBセッションが有効になる場合のみデータ投入する
    if "session" not in request.fixturenames:
        return

    insert_test_data = request.getfixturevalue("insert_test_data")
    default_files = ["companies.sql", "applications.sql", "manuals.sql"]
    insert_test_data(default_files)

@pytest.fixture(scope="session", autouse=True)
def setup_env_vars():
    """テスト実行時の環境変数を設定（LocalStackを使用）"""
    original_env = os.environ.copy()

    # LocalStackへの接続情報
    os.environ["AWS_REGION"] = "ap-northeast-1"
    os.environ["SECRETS_MANAGER_ENDPOINT"] = "http://127.0.0.1:4566"
    os.environ["SSM_ENDPOINT"] = "http://127.0.0.1:4566"
    os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy123"
    os.environ["S3_ENDPOINT"] = "http://127.0.0.1:9002"
    
    # テスト用のMySQL設定をLocalStackに登録
    import json
    secrets_client = boto3.client(
        service_name='secretsmanager',
        region_name="ap-northeast-1",
        endpoint_url="http://127.0.0.1:4566",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy123"
    )
    
    # テスト用のMySQL設定
    # Windows環境では、DockerのMySQL公開ポートが IPv4(127.0.0.1) だと応答しないケースがあり、
    # localhost(IPv6 ::1 優先) の方が安定するため host は "localhost" を利用します。
    mysql_test_config = {
        "user": "root",
        "password": "rootpassword",
        "host": "localhost",
        "port": 3306,
        "database": "db_local",
        "pool_size": 10,
        "max_overflow": 10,
        "pool_timeout": 10,
        "pool_recycle": 10,
        "pool_pre_ping": 1
    }
    
    # 既存のシークレットがある場合は退避して、テスト終了後に復元する
    original_mysql_secret_value = None
    original_mysql_secret_is_binary = False
    mysql_secret_existed = False

    try:
        response = secrets_client.get_secret_value(SecretId="mysql_setting")
        if "SecretBinary" in response:
            original_mysql_secret_value = response["SecretBinary"]
            original_mysql_secret_is_binary = True
        else:
            original_mysql_secret_value = response["SecretString"]
            original_mysql_secret_is_binary = False
        mysql_secret_existed = True
    except ClientError as e:
        if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "InvalidRequestException"]:
            raise

    # テスト用のシークレットを作る前に、既存があれば削除して衝突を避ける
    if mysql_secret_existed:
        try:
            secrets_client.delete_secret(SecretId="mysql_setting", ForceDeleteWithoutRecovery=True)
        except ClientError:
            pass
    
    try:
        # テスト用の設定を作成
        secrets_client.create_secret(
            Name="mysql_setting",
            SecretString=json.dumps(mysql_test_config)
        )
    except Exception as e:
        # すでに存在する場合は更新
        try:
            secrets_client.put_secret_value(
                SecretId="mysql_setting",
                SecretString=json.dumps(mysql_test_config)
            )
        except:
            pass
    
    yield
    
    # クリーンアップ: テスト用のシークレットを削除し、元があれば復元
    try:
        secrets_client.delete_secret(SecretId="mysql_setting", ForceDeleteWithoutRecovery=True)
    except ClientError:
        pass

    if mysql_secret_existed:
        try:
            if original_mysql_secret_is_binary:
                secrets_client.create_secret(Name="mysql_setting", SecretBinary=original_mysql_secret_value)
            else:
                secrets_client.create_secret(Name="mysql_setting", SecretString=original_mysql_secret_value)
        except ClientError:
            pass
    
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def boto_client():
    """テストデータ投入用のBoto3クライアント"""
    return boto3.client(
        service_name='secretsmanager',
        region_name="ap-northeast-1",
        endpoint_url="http://127.0.0.1:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

@pytest.fixture
def managed_secret(boto_client):
    """
    テスト用のシークレットを作成し、テスト終了後に元の値に復元するフィクスチャ
    シークレットが元々存在していた場合は削除せずに元の値を復元する
    """
    @contextlib.contextmanager
    def _managed_secret(name: str, value: str | bytes):
        # 前処理: 既存のシークレットを保存
        original_value = None
        original_is_binary = False
        secret_existed = False
        
        try:
            response = boto_client.get_secret_value(SecretId=name)
            if "SecretBinary" in response:
                original_value = response["SecretBinary"]
                original_is_binary = True
            else:
                original_value = response["SecretString"]
                original_is_binary = False
            secret_existed = True
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "InvalidRequestException"]:
                raise
        
        # 既存のシークレットが存在する場合は削除してから作成
        if secret_existed:
            try:
                boto_client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
            except ClientError:
                pass
        
        # 作成
        try:
            if isinstance(value, bytes):
                boto_client.create_secret(Name=name, SecretBinary=value)
            else:
                boto_client.create_secret(Name=name, SecretString=value)
            
            yield name
        finally:
            # 後処理: 元の値に復元、または削除
            try:
                # 現在のシークレットを削除
                boto_client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
                
                if secret_existed:
                    # 元のシークレットが存在していた場合は復元
                    if original_is_binary:
                        boto_client.create_secret(Name=name, SecretBinary=original_value)
                    else:
                        boto_client.create_secret(Name=name, SecretString=original_value)
            except ClientError:
                pass

    return _managed_secret

@pytest.fixture
def ssm_boto_client():
    """テスト用のSSMクライアント"""
    return boto3.client(
        service_name='ssm',
        region_name="ap-northeast-1",
        endpoint_url="http://127.0.0.1:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

@pytest.fixture
def managed_parameter(ssm_boto_client):
    """
    テスト用のSSMパラメータを作成し、テスト終了後に元の値に復元するフィクスチャ
    パラメータが元々存在していた場合は削除せずに元の値を復元する
    """
    @contextlib.contextmanager
    def _managed_parameter(name: str, value: str, type: str = "String"):
        # 前処理: 既存のパラメータを保存
        original_value = None
        original_type = None
        parameter_existed = False
        
        try:
            response = ssm_boto_client.get_parameter(Name=name)
            original_value = response["Parameter"]["Value"]
            original_type = response["Parameter"]["Type"]
            parameter_existed = True
        except ClientError as e:
            if e.response["Error"]["Code"] != "ParameterNotFound":
                raise

        # 作成または上書き
        try:
            ssm_boto_client.put_parameter(
                Name=name,
                Value=value,
                Type=type,
                Overwrite=True
            )
            yield name
        finally:
            # 後処理: 元の値に復元、または削除
            try:
                if parameter_existed:
                    # 元のパラメータが存在していた場合は復元
                    ssm_boto_client.put_parameter(
                        Name=name,
                        Value=original_value,
                        Type=original_type,
                        Overwrite=True
                    )
                else:
                    # 元々存在しなかった場合は削除
                    ssm_boto_client.delete_parameter(Name=name)
            except ClientError:
                pass

    return _managed_parameter

@pytest.fixture
def deleted_parameter(ssm_boto_client):
    """
    テスト用にSSMパラメータを一時的に削除し、テスト終了後に復元するフィクスチャ
    """
    @contextlib.contextmanager
    def _deleted_parameter(name: str):
        # 前処理: 既存のパラメータを保存して削除
        original_value = None
        original_type = None
        parameter_existed = False
        
        try:
            response = ssm_boto_client.get_parameter(Name=name)
            original_value = response["Parameter"]["Value"]
            original_type = response["Parameter"]["Type"]
            parameter_existed = True
            # パラメータを削除
            ssm_boto_client.delete_parameter(Name=name)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ParameterNotFound":
                raise
        
        try:
            yield name
        finally:
            # 後処理: 元のパラメータを復元
            if parameter_existed:
                try:
                    ssm_boto_client.put_parameter(
                        Name=name,
                        Value=original_value,
                        Type=original_type,
                        Overwrite=True
                    )
                except ClientError:
                    pass

    return _deleted_parameter

@pytest.fixture
def deleted_secret(boto_client):
    """
    テスト用にシークレットを一時的に削除し、テスト終了後に復元するフィクスチャ
    """
    @contextlib.contextmanager
    def _deleted_secret(name: str):
        # 前処理: 既存のシークレットを保存して削除
        original_value = None
        original_is_binary = False
        secret_existed = False
        
        try:
            response = boto_client.get_secret_value(SecretId=name)
            if "SecretBinary" in response:
                original_value = response["SecretBinary"]
                original_is_binary = True
            else:
                original_value = response["SecretString"]
                original_is_binary = False
            secret_existed = True
            # シークレットを削除
            boto_client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "InvalidRequestException"]:
                raise
        
        try:
            yield name
        finally:
            # 後処理: 元のシークレットを復元
            if secret_existed:
                try:
                    if original_is_binary:
                        boto_client.create_secret(Name=name, SecretBinary=original_value)
                    else:
                        boto_client.create_secret(Name=name, SecretString=original_value)
                except ClientError:
                    pass

    return _deleted_secret

@pytest.fixture
def s3_boto_client():
    """テスト用のS3クライアント"""
    return boto3.client(
        service_name='s3',
        region_name="ap-northeast-1",
        endpoint_url="http://127.0.0.1:9002",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy123"
    )

@pytest.fixture
def managed_s3_bucket(s3_boto_client):
    """
    テスト用のS3バケットとオブジェクトを作成し、テスト終了後に削除するフィクスチャ
    """
    @contextlib.contextmanager
    def _managed_s3_bucket(bucket_name: str, files: dict[str, bytes | str] = None):
        # 既存バケットの場合、既存オブジェクトを消さないように事前スナップショットを取る
        bucket_existed = False
        baseline_keys: set[str] = set()

        try:
            s3_boto_client.head_bucket(Bucket=bucket_name)
            bucket_existed = True
        except ClientError:
            bucket_existed = False

        if not bucket_existed:
            try:
                s3_boto_client.create_bucket(Bucket=bucket_name)
            except ClientError:
                # 競合などで既に作られていた場合は既存扱いに寄せる
                bucket_existed = True

        def _list_all_keys() -> set[str]:
            keys: set[str] = set()
            continuation_token = None
            while True:
                kwargs = {"Bucket": bucket_name}
                if continuation_token:
                    kwargs["ContinuationToken"] = continuation_token
                resp = s3_boto_client.list_objects_v2(**kwargs)
                for obj in resp.get("Contents", []) or []:
                    key = obj.get("Key")
                    if key:
                        keys.add(key)
                if resp.get("IsTruncated"):
                    continuation_token = resp.get("NextContinuationToken")
                    continue
                break
            return keys

        try:
            baseline_keys = _list_all_keys()
        except ClientError:
            baseline_keys = set()

        # ファイルアップロード
        if files:
            for key, content in files.items():
                if isinstance(content, str):
                    content = content.encode('utf-8')
                s3_boto_client.put_object(Bucket=bucket_name, Key=key, Body=content)

        yield bucket_name

        # 後処理: テスト中に増えたオブジェクトのみ削除（既存データは保持）
        try:
            current_keys = _list_all_keys()
            keys_to_delete = sorted(current_keys - baseline_keys)

            # delete_objects は最大 1000 件ずつ
            for i in range(0, len(keys_to_delete), 1000):
                chunk = keys_to_delete[i:i + 1000]
                s3_boto_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": [{"Key": k} for k in chunk]}
                )

            # このフィクスチャが新規作成したバケットだけ削除する
            if not bucket_existed:
                s3_boto_client.delete_bucket(Bucket=bucket_name)
        except ClientError:
            pass

    return _managed_s3_bucket

@pytest.fixture(scope="function")
def setup_postgresql_test_collection():
    """
    PostgreSQL Vector DBのテスト用コレクションをセットアップするフィクスチャ
    テスト終了後にコレクションをクリーンアップする
    """
    
    # PostgreSQL接続情報（docker-compose.ymlの設定に合わせる）
    connection_string = "postgresql+psycopg://vector_user:vector_password@localhost:5432/vector_db"
    engine = create_engine(connection_string)
    
    test_collection_name = "test_manuals"
    
    # 前処理: 既存のテストコレクションをクリーンアップ
    with engine.connect() as conn:
        # コレクションIDを取得
        result = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": test_collection_name}
        )
        collection = result.fetchone()
        
        if collection:
            collection_id = collection[0]
            # 関連する埋め込みデータを削除
            conn.execute(
                text("DELETE FROM langchain_pg_embedding WHERE collection_id = :id"),
                {"id": collection_id}
            )
            # コレクションを削除
            conn.execute(
                text("DELETE FROM langchain_pg_collection WHERE uuid = :id"),
                {"id": collection_id}
            )
            conn.commit()
    
    yield test_collection_name
    
    # 後処理: テストコレクションをクリーンアップ
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": test_collection_name}
        )
        collection = result.fetchone()
        
        if collection:
            collection_id = collection[0]
            conn.execute(
                text("DELETE FROM langchain_pg_embedding WHERE collection_id = :id"),
                {"id": collection_id}
            )
            conn.execute(
                text("DELETE FROM langchain_pg_collection WHERE uuid = :id"),
                {"id": collection_id}
            )
            conn.commit()
    
    engine.dispose()

@pytest.fixture
def setup_test_parameters(managed_secret, managed_parameter, deleted_secret, deleted_parameter):
    """
    テスト用のパラメータとシークレットをセットアップするヘルパーフィクスチャ
    Noneの場合は削除、それ以外の場合は設定する
    
    使用例:
        with setup_test_parameters(
            postgresql_config=config,
            llm_config=None,  # 削除
            embedding_config=config
        ):
            # テストコード
    """
    @contextlib.contextmanager
    def _setup(
        postgresql_config=None,
        llm_config=None,
        embedding_config=None,
        question_llm_config=None
    ):
        import json
        
        contexts = []
        
        # PostgreSQL設定
        if postgresql_config is None:
            contexts.append(deleted_secret("postgresql_setting"))
        else:
            contexts.append(managed_secret("postgresql_setting", json.dumps(postgresql_config)))
        
        # LLM設定
        if llm_config is None:
            contexts.append(deleted_parameter("llm_setting"))
        else:
            contexts.append(managed_parameter("llm_setting", json.dumps(llm_config)))
        
        # Embedding設定
        if embedding_config is None:
            contexts.append(deleted_parameter("embedding_setting"))
        else:
            contexts.append(managed_parameter("embedding_setting", json.dumps(embedding_config)))
        
        # Question LLM設定（オプショナル）
        if question_llm_config is False:
            # Falseの場合は明示的に削除
            contexts.append(deleted_parameter("question_llm_setting"))
        elif question_llm_config is not None:
            # 値が設定されている場合は設定
            contexts.append(managed_parameter("question_llm_setting", json.dumps(question_llm_config)))
        # Noneの場合は何もしない（既存の設定を保持）
        
        # ネストされたコンテキストマネージャーを実行
        def enter_contexts(contexts_list, index=0):
            if index >= len(contexts_list):
                yield
            else:
                with contexts_list[index]:
                    yield from enter_contexts(contexts_list, index + 1)
        
        yield from enter_contexts(contexts)
    
    return _setup
