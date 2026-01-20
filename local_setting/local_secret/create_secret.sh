#!/bin/sh
set -e

DATA_DIR="/init/secret_data"

echo 'LocalStackの起動を待っています...'
until aws --endpoint-url=http://localstack:4566 secretsmanager list-secrets >/dev/null 2>&1; do
  sleep 1;
done;

echo 'LocalStackの準備ができました。シークレットを投入中...'

if [ -d "$DATA_DIR" ]; then
    for file in "$DATA_DIR"/*.json; do
        if [ -f "$file" ]; then
            secret_name=$(basename "$file" .json)
            echo "シークレットを作成中: $secret_name"
            
            # シークレットが既に存在するか確認して作成または更新
            if aws --endpoint-url=http://localstack:4566 secretsmanager describe-secret --secret-id "$secret_name" >/dev/null 2>&1; then
                echo "シークレット $secret_name は既に存在します。更新中..."
                aws --endpoint-url=http://localstack:4566 secretsmanager put-secret-value \
                    --secret-id "$secret_name" \
                    --secret-string "file://$file"
            else
                echo "シークレット $secret_name は存在しません。作成中..."
                aws --endpoint-url=http://localstack:4566 secretsmanager create-secret \
                    --name "$secret_name" \
                    --secret-string "file://$file"
            fi
        fi
    done
else
    echo "シークレットデータディレクトリが見つかりません: $DATA_DIR"
fi

echo 'シークレットの投入が完了しました。'
