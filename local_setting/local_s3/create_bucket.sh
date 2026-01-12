#!/bin/sh
# busyboxでも動くようにPOSIXシェルのみで実装
set -eu

SRC_DIR="/init/local_buckets"  # バケット構成のルート（ホストからマウント）

echo "⏳ MinIOの起動を待っています..."
# MinIOが応答するまでalias設定をリトライ
until mc alias set local http://navi-api-s3:9000 dummy dummy123 >/dev/null 2>&1; do
  sleep 1
done
echo "✅ MinIOのエイリアスを設定しました。"

# CORS設定を一時ファイルに出力
cat >/tmp/cors.json <<'JSON'
[
  {
    "AllowedOrigin": ["*"],
    "AllowedMethod": ["GET","HEAD"],
    "AllowedHeader": ["*"],
    "ExposeHeader": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
JSON

if [ ! -d "$SRC_DIR" ]; then
  echo "ℹ️ ソースディレクトリが見つかりません: $SRC_DIR (作成/アップロードなし)"
  exit 0
fi

created_any=false

# local_backets直下の各ディレクトリ名をバケット名として扱い、内容をミラーリング
for path in "$SRC_DIR"/*; do
  [ -d "$path" ] || continue
  bucket=$(basename "$path")

  echo "🪣 バケットが存在することを確認中: $bucket"
  # 既存なら成功扱い
  mc mb --ignore-existing "local/$bucket" >/dev/null 2>&1 || true

  echo "📤 $pathからs3://$bucketへオブジェクトをアップロード中..."
  # 変更があれば上書き、再実行しても冪等
  mc mirror --overwrite "$path" "local/$bucket" || true

  echo "🔓 公開設定(匿名GET)を適用中: $bucket"
  mc anonymous set download "local/$bucket" || true

  echo "🌐 CORS設定を適用中: $bucket"
  mc cors set "local/$bucket" /tmp/cors.json || true

  created_any=true
done

if [ "$created_any" = false ]; then
  echo "ℹ️ バケットディレクトリが見つかりません: $SRC_DIR"
else
  echo "🎉 バケット作成、オブジェクトアップロード、公開設定、CORS設定が完了しました。"
fi
