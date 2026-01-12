#!/bin/sh
set -e

DATA_DIR="/init/ssm_data"

echo 'LocalStack SSMの起動を待っています...'
until aws --endpoint-url=http://localstack:4566 ssm describe-parameters >/dev/null 2>&1; do
  sleep 1;
done;

echo 'LocalStack SSMの準備ができました。パラメータを投入中...'

if [ -d "$DATA_DIR" ]; then
    for file in "$DATA_DIR"/*.json; do
        if [ -f "$file" ]; then
            parameter_name=$(basename "$file" .json)
            echo "パラメータを作成中: $parameter_name"
            
            # パラメータが既に存在するか確認して作成または更新
            if aws --endpoint-url=http://localstack:4566 ssm get-parameter --name "$parameter_name" >/dev/null 2>&1; then
                echo "パラメータ $parameter_name は既に存在します。更新中..."
                aws --endpoint-url=http://localstack:4566 ssm put-parameter \
                    --name "$parameter_name" \
                    --value "file://$file" \
                    --type "String" \
                    --overwrite
            else
                echo "パラメータ $parameter_name は存在しません。作成中..."
                aws --endpoint-url=http://localstack:4566 ssm put-parameter \
                    --name "$parameter_name" \
                    --value "file://$file" \
                    --type "String"
            fi
        fi
    done
else
    echo "SSMデータディレクトリが見つかりません: $DATA_DIR"
fi

echo 'パラメータの投入が完了しました。'