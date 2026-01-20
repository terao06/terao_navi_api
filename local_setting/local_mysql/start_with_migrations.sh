#!/bin/bash
set -e

# バックグラウンドでマイグレーション実行処理を開始
(
    echo "バックグラウンドでマイグレーション実行処理を開始します..."
    # Pythonスクリプトがデータベース接続を待機する処理を行う
    python3 /docker-entrypoint-initdb.d/99-run-migrations.py
) &

# 元のエントリーポイントを実行
# これによりMySQLが起動する
exec /usr/local/bin/docker-entrypoint.sh "$@"
