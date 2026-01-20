from app.models.llm.base_llm_model import BaseLLMModel
from app.core.aws.s3_client import S3Client
from app.core.logging import NaviApiLog

def init_vectors():
    """
    local_data/minio/manuals 配下のPDFファイルを走査し、
    一括でVector DBに登録するスクリプト。
    """
    NaviApiLog.info("マニュアルでベクトルデータベースを初期化しています...")
    
    # ローカルのMinIOデータフォルダ (docker-composeのvolumes構成に依存)
    # navi-api-appコンテナからは MinIOは見えないため、単純にS3クライアント経由で取得するのが正しいが、
    # ここでは「初期化」として、まずバケット内の全ファイルを取得するロジックを組む。
    
    bucket_name = "manuals"
    
    # 既存のS3Clientなどを利用してバケット内のファイル一覧を取得
    # S3上のファイルを全て登録したい場合:
    try:
        s3 = S3Client()
        # バケット内のオブジェクトをリストアップ（プレフィックスなしで全件）
        objects = s3.list_objects(bucket_name=bucket_name)
        
        file_paths = []
        if objects:
            for obj in objects:
                # S3のキーを取得（例: "1/100.pdf"）
                key = obj['Key']
                # PDFファイルのみ対象にする等のフィルタが必要ならここに記述
                if key.endswith('.pdf'):
                    # LangChainのS3FileLoaderはbucket引数とkey引数を別々に取るため
                    # ここではkeyのみをリストに追加する
                    file_paths.append(key)
        
        if not file_paths:
            NaviApiLog.warning(f"バケット'{bucket_name}'にPDFファイルが見つかりませんでした。")
            return

        NaviApiLog.info(f"バケット内に{len(file_paths)}個のファイルが見つかりました。")
        
        # BaseLLMModelを初期化して、既存のベクトル化済みファイルを取得
        llm_wrapper = BaseLLMModel_InitWrapper([], collection_name="manuals")
        existing_sources = llm_wrapper.get_existing_sources()
        NaviApiLog.info(f"ベクトルストア内に{len(existing_sources)}個の既存ドキュメントが見つかりました。")
        
        # 未ベクトル化のファイルのみをフィルタリング
        new_file_paths = []
        for file_path in file_paths:
            source_key = f"{bucket_name}/{file_path}"
            if source_key not in existing_sources:
                new_file_paths.append(file_path)
            else:
                NaviApiLog.debug(f"既にベクトル化済みのファイルをスキップします: {source_key}")
        
        if not new_file_paths:
            NaviApiLog.info("全てのファイルが既にベクトル化されています。追加するファイルはありません。")
            return
        
        NaviApiLog.info(f"全{len(file_paths)}ファイル中、{len(new_file_paths)}個の新規ファイルを処理します。")
        
        # 未ベクトル化のファイルのみを登録
        llm_wrapper.ingest_documents(bucket_name, new_file_paths)
        
        NaviApiLog.info("ベクトルデータベースの初期化が正常に完了しました。")

    except Exception as e:
        NaviApiLog.error(f"ベクトルの初期化に失敗しました: {e}")

# BaseLLMModelは抽象メソッドがあるため、そのままではインスタンス化できない。
# 初期化用にダミーの具象クラスを定義する。
class BaseLLMModel_InitWrapper(BaseLLMModel):
    def get_graph(self):
        return None

if __name__ == "__main__":
    init_vectors()
