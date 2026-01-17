#!/usr/bin/env pwsh
# Docker環境を管理するスクリプト
# 使い方: .\make.ps1 [コマンド]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# BuildKit を有効化
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

switch ($Command) {
    "up" {
        Write-Host "🚀 BuildKitを有効化してコンテナを起動中..." -ForegroundColor Green
        docker compose up
    }
    "up-d" {
        Write-Host "🚀 BuildKitを有効化してコンテナをバックグラウンドで起動中..." -ForegroundColor Green
        docker compose up -d
    }
    "up-build" {
        Write-Host "🚀 BuildKitを有効化してコンテナを起動中..." -ForegroundColor Green
        docker compose up --build
    }
    "up-d-build" {
        Write-Host "🚀 BuildKitを有効化してコンテナをバックグラウンドで起動中..." -ForegroundColor Green
        docker compose up -d --build
    }
    "down" {
        Write-Host "⏹️  コンテナを停止中..." -ForegroundColor Yellow
        docker compose down
    }
    "build" {
        Write-Host "🔨 BuildKitを使用してイメージをビルド中..." -ForegroundColor Green
        docker compose build
    }
    "rebuild" {
        Write-Host "🧹 クリーンビルドを実行中（キャッシュを削除）..." -ForegroundColor Green
        docker compose down --rmi local
        docker compose build --no-cache
        docker compose up -d
    }
    "logs" {
        Write-Host "📋 全サービスのログを表示中..." -ForegroundColor Cyan
        docker compose logs -f
    }
    "logs-app" {
        Write-Host "📋 アプリケーションのログを表示中..." -ForegroundColor Cyan
        docker compose logs -f navi-api-app
    }
    "clean" {
        Write-Host "🗑️  すべてのコンテナ・イメージ・ボリュームを削除中..." -ForegroundColor Red
        docker compose down --rmi all --volumes --remove-orphans
    }
    "ps" {
        Write-Host "📊 コンテナの状態:" -ForegroundColor Cyan
        docker compose ps
    }
    "restart" {
        Write-Host "🔄 コンテナを再起動中..." -ForegroundColor Yellow
        docker compose restart
    }
    "stop" {
        Write-Host "⏸️  コンテナを停止中..." -ForegroundColor Yellow
        docker compose stop
    }
    "start" {
        Write-Host "▶️  停止したコンテナを起動中..." -ForegroundColor Green
        docker compose start
    }
    "help" {
        Write-Host "📚 利用可能なコマンド:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  .\make.ps1 up          - コンテナを起動（フォアグラウンド）" -ForegroundColor White
        Write-Host "  .\make.ps1 up-d        - コンテナを起動（バックグラウンド）" -ForegroundColor White
        Write-Host "  .\make.ps1 down        - コンテナを停止して削除" -ForegroundColor White
        Write-Host "  .\make.ps1 build       - イメージのみビルド" -ForegroundColor White
        Write-Host "  .\make.ps1 rebuild     - クリーンビルド（キャッシュ削除）" -ForegroundColor White
        Write-Host "  .\make.ps1 logs        - 全サービスのログを表示" -ForegroundColor White
        Write-Host "  .\make.ps1 logs-app    - アプリケーションのログのみ表示" -ForegroundColor White
        Write-Host "  .\make.ps1 clean       - すべて削除（コンテナ/イメージ/ボリューム）" -ForegroundColor White
        Write-Host "  .\make.ps1 ps          - コンテナの状態を表示" -ForegroundColor White
        Write-Host "  .\make.ps1 restart     - コンテナを再起動" -ForegroundColor White
        Write-Host "  .\make.ps1 stop        - コンテナを停止" -ForegroundColor White
        Write-Host "  .\make.ps1 start       - 停止したコンテナを起動" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 BuildKitは自動的に有効化され、ビルドが高速化されます" -ForegroundColor Green
    }
    default {
        Write-Host "❌ 不明なコマンド: $Command" -ForegroundColor Red
        Write-Host "利用可能なコマンドを確認するには '.\make.ps1 help' を実行してください" -ForegroundColor Yellow
    }
}
