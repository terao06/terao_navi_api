# Terao Navi API

このプロジェクトは、FastAPIを使用したナビゲーションAPIアプリケーションです。LLMとベクトルデータベースを活用した質問応答システムを提供します。

## 目次

- [前提条件](#前提条件)
- [システム構成](#システム構成)
- [プロジェクト構成](#プロジェクト構成)
- [初期設定](#初期設定)
  - [1. Embeddingモデルの準備](#1-embeddingモデルの準備)
  - [2. 設定ファイルの編集](#2-設定ファイルの編集)
  - [3. 認証情報の確認](#3-認証情報の確認)
- [アプリケーションの起動](#アプリケーションの起動)
- [動作確認](#動作確認)
- [停止と再起動](#停止と再起動)
- [開発時の注意事項](#開発時の注意事項)
- [ライセンス](#ライセンス)

## 前提条件

以下のソフトウェアがインストールされている必要があります：

- Docker Desktop (Windows/Mac) または Docker Engine (Linux)
- Docker Compose
- Git

### 環境変数 (.env)

プロジェクトルートに `.env` ファイルを置いています。現在の設定例:

```
COMPOSE_PARALLEL_LIMIT=2
```

理由: `COMPOSE_PARALLEL_LIMIT` は Docker Compose の並列実行数を制限する環境変数です。ローカル開発マシン（特にメモリや CPU に制約がある Windows ノートPC）で複数コンテナを同時にビルド／起動するとリソース競合やビルド失敗、OOM（メモリ不足）を引き起こすことがあります。並列数を 2 に制限することでビルド／起動の安定性が向上します。

注意: 必要に応じてこの値を増減してください（例: 高性能マシンでは `4` など）。

## システム構成
### 構成図
![システム構成図](docs/diagram.svg)


### 解説
- `navi-api-app` : FastAPIアプリケーション。エンドポイントは外部クライアント（ブラウザ、curl、APIクライアント）からのHTTPを受け付けます。
- `navi-api-db` : MySQL。アプリの主な永続データを保持します（ユーザー、マニュアル等）。
- `navi-api-minio` : S3互換ストレージ。ファイル、マニュアルPDFやアセットを保存します。
- `navi-api-vector-db` : ベクトル検索用のPostgres（拡張）など。埋め込みベクトルの保存・検索を担当します。
- `navi-api-dynamodb` : ローカルDynamoDB（必要に応じて）。
- `local_setting/local_app/llm_models` はコンテナ内部に `/models` としてマウントされ、埋め込みモデルやローカルLLMモデルの配置先になります。embedding_setting.json の `model_name` はコンテナ内のパス（例: `/models/bge-m3`）を指すようにしてください。

## プロジェクト構成

```
terao_navi_api/
├── app/                          # アプリケーションコード
│   ├── main.py                   # FastAPIエントリーポイント
│   ├── api/                      # APIエンドポイント
│   ├── core/                     # コア機能（DB、AWS接続など）
│   ├── models/                   # データモデル
│   ├── services/                 # ビジネスロジック
│   └── repositories/             # データアクセス層
├── local_setting/                # ローカル開発用設定
│   ├── local_app/
│   │   └── llm_models/          # Embeddingモデル格納ディレクトリ
│   ├── local_ssm/
│   │   └── ssm_data/            # LLM/Embedding設定ファイル
│   └── local_secret/
│       └── secret_data/         # データベース接続情報など
├── local_data/                   # 永続化データ
│   ├── credential/              # API認証情報
│   ├── mysql/                   # MySQLデータ
│   ├── minio/                   # S3互換ストレージ
│   └── vector_db/               # PostgreSQLベクトルDB
├── docker-compose.yml           # Docker構成ファイル
├── requirements.txt             # Python依存関係
└── README.md                    # このファイル
```

## 初期設定

### 1. Embeddingモデルの準備

プロジェクトを初めて起動する前に、Embeddingモデルをダウンロードして配置する必要があります。

#### 推奨モデル：BGE-M3

1. **Hugging Faceからモデルをダウンロード**
   
   [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3/tree/main)からモデルファイルをダウンロードします。

   ```powershell
   # Git LFSがインストールされている場合
   cd local_setting\local_app\llm_models
   git lfs install
   git clone https://huggingface.co/BAAI/bge-m3
   ```

   または、Hugging Faceのウェブサイトから手動でダウンロードすることもできます。

2. **モデルの配置**
   
   ダウンロードしたモデルを以下のディレクトリに配置します：
   
   ```
   local_setting/local_app/llm_models/bge-m3/
   ├── config.json
   ├── model.safetensors
   ├── tokenizer_config.json
   ├── tokenizer.json
   ├── vocab.txt
   └── ...その他のモデルファイル
   ```

   **注意**: ディレクトリ名は任意ですが、次のステップで設定ファイルに正確なパスを記載する必要があります。

#### その他のモデル

以下のようなモデルも使用可能です：
- `intfloat/multilingual-e5-large`
- `sentence-transformers/all-MiniLM-L6-v2`

### 2. 設定ファイルの編集

#### 2.1 Embedding設定

`local_setting/local_ssm/ssm_data/embedding_setting.json`を編集します：

```json
{
    "model_name": "/models/bge-m3"
}
```

- `model_name`: コンテナ内のモデルパスを指定
- コンテナ内では `/models/` ディレクトリに `local_setting/local_app/llm_models/` がマウントされます
- 例: `local_setting/local_app/llm_models/bge-m3/` → `/models/bge-m3`

#### 2.2 LLM設定

`local_setting/local_ssm/ssm_data/llm_setting.json`を編集します：

**デフォルト設定（Ollamaサーバー使用）:**
```json
{
    "model_name": "gpt-oss:20b",
    "base_url": "http://host.docker.internal:11434/v1",
    "api_key": "dummy_api_key",
    "temperature": 0.7
}
```

**ChatGPT API使用の場合:**
```json
{
    "model_name": "gpt-4",
    "base_url": "https://api.openai.com/v1",
    "api_key": "YOUR_OPENAI_API_KEY",
    "temperature": 0.7
}
```

- `model_name`: 使用するモデル名
- `base_url`: APIのベースURL
- `api_key`: APIキー（OpenAI、Ollamaなど）
- `temperature`: 生成の多様性（0.0〜1.0）

#### 2.3 その他の設定ファイル

以下のファイルも必要に応じて編集できます：

- `local_setting/local_ssm/ssm_data/question_llm_setting.json`: 質問処理用のLLM設定
- `local_setting/local_secret/secret_data/mysql_setting.json`: MySQL接続情報
- `local_setting/local_secret/secret_data/postgresql_setting.json`: PostgreSQL接続情報

### 3. 認証情報の確認

コンテナ起動時、以下のファイルにAPI動作確認用の認証情報が自動的に生成されます：

```
local_data/credential/test_credential.txt
```

このファイルには以下の情報が含まれます：
```
client_id=<クライアントID>
client_secret=<クライアントシークレット>
```

**重要**: 
- この認証情報は**コンテナ初回起動時に自動的に生成**されます
- 動作確認用の**初期データ（テストユーザー、サンプルデータなど）も自動的にデータベースに登録**されます
- これらの認証情報とデータはテスト・開発用です。本番環境では適切な認証メカニズムを実装してください

## アプリケーションの起動

### 1. Dockerコンテナの起動

プロジェクトのルートディレクトリで以下のコマンドを実行します：

**Windows (PowerShell):**
```powershell
# コンテナをビルドして起動（バックグラウンド）
.\make.ps1 up-d

# または、フォアグラウンドで起動（ログをリアルタイム表示）
.\make.ps1 up
```

**Mac/Linux:**
```bash
# コンテナをビルドして起動（バックグラウンド）
make up-d

# または、フォアグラウンドで起動（ログをリアルタイム表示）
make up
```

初回起動時は、以下の処理が実行されます：
- Dockerイメージのビルド（BuildKitによる高速ビルド）
- データベースの初期化
- マイグレーションの実行
- **動作確認用の初期データ（認証情報、テストユーザー等）の自動登録**
- 必要なサービスの起動

### 2. 起動確認

コンテナの状態を確認します：

**Windows (PowerShell):**
```powershell
.\make.ps1 ps
```

**Mac/Linux:**
```bash
make ps
```

すべてのサービスが `running` 状態になっていることを確認してください。

### 3. ログの確認

アプリケーションのログを確認します：

**Windows (PowerShell):**
```powershell
# すべてのログを表示
.\make.ps1 logs

# APIアプリケーションのログのみ表示
.\make.ps1 logs-app
```

**Mac/Linux:**
```bash
# すべてのログを表示
make logs

# APIアプリケーションのログのみ表示
make logs-app
```

### 利用可能なMakeコマンド

| コマンド | 説明 |
|---------|------|
| `up` | コンテナを起動（フォアグラウンド） |
| `up-d` | コンテナを起動（バックグラウンド） |
| `down` | コンテナを停止して削除 |
| `build` | イメージのみビルド |
| `rebuild` | クリーンビルド（キャッシュ削除） |
| `logs` | 全サービスのログを表示 |
| `logs-app` | アプリケーションのログのみ表示 |
| `clean` | すべて削除（コンテナ/イメージ/ボリューム） |
| `ps` | コンテナの状態を表示 |
| `restart` | コンテナを再起動 |
| `stop` | コンテナを停止 |
| `start` | 停止したコンテナを起動 |
| `help` | ヘルプを表示 |

**Windows:** `.\make.ps1 [コマンド]`  
**Mac/Linux:** `make [コマンド]`

## 動作確認

### 1. ヘルスチェック

APIが正常に起動しているか確認します：

```powershell
# PowerShellの場合
Invoke-WebRequest -Uri http://localhost:8005/health
```

または、ブラウザで以下のURLにアクセス：
```
http://localhost:8005/docs
```

FastAPIの自動生成されたAPIドキュメント（Swagger UI）が表示されます。

### 2. サービスへのアクセス

以下のサービスにアクセスできます：

| サービス | URL | 説明 |
|---------|-----|------|
| API | http://localhost:8005 | FastAPI アプリケーション |
| API Docs | http://localhost:8005/docs | Swagger UI |
| phpMyAdmin | http://localhost:8080 | MySQL管理画面 |
| MinIO Console | http://localhost:9003 | S3互換ストレージ管理画面 |
| pgAdmin | http://localhost:8082 | PostgreSQL管理画面 |

#### ログイン情報

**phpMyAdmin:**
- サーバー: `navi-api-db`
- ユーザー名: `navi_admin_user`
- パスワード: `password`

**MinIO Console:**
- ユーザー名: `dummy`
- パスワード: `dummy123`

**pgAdmin:**
- Email: `admin@example.com`
- パスワード: `admin`

### 3. API呼び出しテスト

認証情報を使用してAPIをテストします：

```powershell
# 認証情報を読み込む
$credential = Get-Content local_data\credential\test_credential.txt
$clientId = ($credential | Select-String "client_id=(.+)").Matches.Groups[1].Value
$clientSecret = ($credential | Select-String "client_secret=(.+)").Matches.Groups[1].Value

# Bearerトークンを作成（client_id:client_secret形式）
$token = "${clientId}:${clientSecret}"

# APIリクエストの例（エンドポイントに応じて変更してください）
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Invoke-WebRequest -Uri http://localhost:8005/api/v1/question -Method POST -Headers $headers -Body '{"question": "テスト質問"}'
```

**認証方式**: `Authorization: Bearer client_id:client_secret`

例:
```
Authorization: Bearer adb83002d4d9a6e362df4bf6b899db7c:f53e8aa23f072d5367915ebcea2bc3cd099968c354662ecc9bd03bc950a26ce0
```

## 停止と再起動

### コンテナの停止

**Windows (PowerShell):**
```powershell
.\make.ps1 down
```

**Mac/Linux:**
```bash
make down
```

### データを保持したまま停止

**Windows (PowerShell):**
```powershell
.\make.ps1 stop
```

**Mac/Linux:**
```bash
make stop
```

### 再起動

**Windows (PowerShell):**
```powershell
# 停止したコンテナを再起動
.\make.ps1 start

# または、完全に再起動
.\make.ps1 restart
```

**Mac/Linux:**
```bash
# 停止したコンテナを再起動
make start

# または、完全に再起動
make restart
```

### データを完全に削除して再起動

**Windows (PowerShell):**
```powershell
# コンテナ、イメージ、ボリュームを削除
.\make.ps1 clean

# 再度起動
.\make.ps1 up-d
```

**Mac/Linux:**
```bash
# コンテナ、イメージ、ボリュームを削除
make clean

# 再度起動
make up-d
```

### キャッシュをクリアして再ビルド

**Windows (PowerShell):**
```powershell
.\make.ps1 rebuild
```

**Mac/Linux:**
```bash
make rebuild
```

## 開発時の注意事項

### ホットリロード

アプリケーションコードを変更すると、自動的にリロードされます（`--reload` オプションが有効）。

### Python依存関係の追加

新しいパッケージを追加した場合：

1. `requirements.txt` を編集
2. コンテナを再ビルド:
   - **Windows:** `.\make.ps1 rebuild`
   - **Mac/Linux:** `make rebuild`

### データベーススキーマの変更

マイグレーションファイルを `local_setting/local_mysql/migrations/` に配置し、コンテナを再起動してください。  
※ API内ではSQLAlchemyを使用していますが、管理画面をDjangoで実装しているためDBのスキーマもDjangoの仕様となっています。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。
