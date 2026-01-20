.PHONY: up up-d down build rebuild logs logs-app clean ps restart stop start help

# デフォルトターゲット
.DEFAULT_GOAL := help

# BuildKit環境変数を設定
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

## up: コンテナを起動（フォアグラウンド）
up:
	@echo "🚀 BuildKitを有効化してコンテナを起動中..."
	docker compose up

## up-d: コンテナを起動（ビルド + バックグラウンド）
up-d:
	@echo "🚀 BuildKitを有効化してコンテナをバックグラウンドで起動中..."
	docker compose up -d

## up-build: コンテナを起動（ビルド + フォアグラウンド）
up-build:
	@echo "🚀 BuildKitを有効化してコンテナを起動中..."
	docker compose up --build

## up-d: コンテナを起動（バックグラウンド）
up--build-d:
	@echo "🚀 BuildKitを有効化してコンテナをバックグラウンドで起動中..."
	docker compose up -d --build

## down: コンテナを停止
down:
	@echo "⏹️  コンテナを停止中..."
	docker compose down

## build: イメージをビルド（起動しない）
build:
	@echo "🔨 BuildKitを使用してイメージをビルド中..."
	docker compose build

## rebuild: クリーンビルド（既存イメージ削除してビルド）
rebuild:
	@echo "🧹 クリーンビルドを実行中（キャッシュを削除）..."
	docker compose down --rmi local
	docker compose build --no-cache
	docker compose up -d

## logs: ログを表示（全サービス）
logs:
	@echo "📋 全サービスのログを表示中..."
	docker compose logs -f

## logs-app: アプリケーションのログを表示
logs-app:
	@echo "📋 アプリケーションのログを表示中..."
	docker compose logs -f navi-api-app

## clean: すべてのコンテナ・イメージ・ボリュームを削除
clean:
	@echo "🗑️  すべてのコンテナ・イメージ・ボリュームを削除中..."
	docker compose down --rmi all --volumes --remove-orphans

## ps: コンテナの状態を表示
ps:
	@echo "📊 コンテナの状態:"
	docker compose ps

## restart: コンテナを再起動
restart:
	@echo "🔄 コンテナを再起動中..."
	docker compose restart

## stop: コンテナを停止（削除はしない）
stop:
	@echo "⏸️  コンテナを停止中..."
	docker compose stop

## start: 停止したコンテナを起動
start:
	@echo "▶️  停止したコンテナを起動中..."
	docker compose start

## help: このヘルプを表示
help:
	@echo "📚 利用可能なコマンド:"
	@echo ""
	@echo "  make up          - コンテナを起動（フォアグラウンド）"
	@echo "  make up-d        - コンテナを起動（バックグラウンド）"
	@echo "  make down        - コンテナを停止して削除"
	@echo "  make build       - イメージのみビルド"
	@echo "  make rebuild     - クリーンビルド（キャッシュ削除）"
	@echo "  make logs        - 全サービスのログを表示"
	@echo "  make logs-app    - アプリケーションのログのみ表示"
	@echo "  make clean       - すべて削除（コンテナ/イメージ/ボリューム）"
	@echo "  make ps          - コンテナの状態を表示"
	@echo "  make restart     - コンテナを再起動"
	@echo "  make stop        - コンテナを停止"
	@echo "  make start       - 停止したコンテナを起動"
	@echo ""
	@echo "💡 BuildKitは自動的に有効化され、ビルドが高速化されます"
