#!/usr/bin/env bash
set -euo pipefail

# ===== 設定（composeのenvironmentから上書きされます）=====
ENDPOINT="${DDB_ENDPOINT:-http://navi-api-dynamodb:8000}"
REGION="${AWS_REGION:-ap-northeast-1}"
TABLE_PREFIX="${DDB_TABLE_PREFIX:-}"

# ===== テーブル名 =====
ASM_TABLE="${TABLE_PREFIX}agent_session_messages"
ASS_TABLE="${TABLE_PREFIX}agent_session_states"

echo "[init] endpoint=${ENDPOINT} region=${REGION} prefix=${TABLE_PREFIX}"

# Python3のインストールチェックとインストール
if ! command -v python3 >/dev/null 2>&1; then
  echo "[init] python3が見つかりません。インストール中..."
  if command -v yum >/dev/null 2>&1; then
    yum install -y python3
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y python3
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache python3
  else
    echo "[init] エラー: パッケージマネージャーが見つかりません。python3をインストールできません。" >&2
    exit 1
  fi
fi

# ----- DynamoDB Local起動待ち -----
echo "[init] DynamoDBの起動を待っています..."
for i in {1..10}; do
  if aws dynamodb list-tables --endpoint-url "${ENDPOINT}" --region "${REGION}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# =========================
# auth_clients
# =========================
AUTH_TABLE="${TABLE_PREFIX}auth_clients"

if aws dynamodb describe-table \
    --table-name "${AUTH_TABLE}" \
    --endpoint-url "${ENDPOINT}" --region "${REGION}" >/dev/null 2>&1; then
  echo "[init] テーブルが既に存在します: ${AUTH_TABLE}"
else
  echo "[init] テーブルを作成中: ${AUTH_TABLE}"
  aws dynamodb create-table \
    --table-name "${AUTH_TABLE}" \
    --billing-mode PAY_PER_REQUEST \
    --attribute-definitions \
      AttributeName=client_id,AttributeType=S \
      AttributeName=company_id,AttributeType=N \
    --key-schema \
      AttributeName=client_id,KeyType=HASH \
    --global-secondary-indexes '[
      {
        "IndexName": "idx_company_id",
        "KeySchema": [{"AttributeName":"company_id","KeyType":"HASH"}],
        "Projection": {"ProjectionType":"ALL"}
      }
    ]' \
    --endpoint-url "${ENDPOINT}" --region "${REGION}"
  echo "[init] テーブルを作成しました: ${AUTH_TABLE}"
fi

# =========================
# 初期データ
# =========================
# 初期データが無い場合は必ず作成する
# 既存判定はcompany_idのGSI(idx_company_id)で行う

AUTH_COMPANY_ID="${AUTH_COMPANY_ID:-1}"
AUTH_CLIENT_NAME="${AUTH_CLIENT_NAME:-local-dev}"
AUTH_STATUS="${AUTH_STATUS:-active}"

echo "[init] 初期データの必要性を確認中... company_id=${AUTH_COMPANY_ID}"

EXISTING_COUNT="$(
  aws dynamodb query \
    --table-name "${AUTH_TABLE}" \
    --index-name "idx_company_id" \
    --key-condition-expression "company_id = :cid" \
    --expression-attribute-values "{\":cid\": {\"N\": \"${AUTH_COMPANY_ID}\"}}" \
    --select "COUNT" \
    --query "Count" --output text \
    --endpoint-url "${ENDPOINT}" --region "${REGION}" 2>/dev/null || echo "0"
)"

EXISTING_COUNT="${EXISTING_COUNT:-0}"

if [[ "${EXISTING_COUNT}" != "0" ]]; then
  echo "[init] 初期データ投入をスキップしました: company_id=${AUTH_COMPANY_ID}の認証クライアントが既に存在します (count=${EXISTING_COUNT})"
else
  echo "[init] 認証クライアントの初期データを投入中... company_id=${AUTH_COMPANY_ID} name=${AUTH_CLIENT_NAME}"

  # credential.pyを使用して生成
  CRED_OUTPUT=$(PYTHONPATH=/work python3 -c "
import sys
try:
    from app.core.utils.credential_util import CredentialUtil
    cid, csec, chash = CredentialUtil.generate_client_credential()
    print(f'{cid} {csec} {chash}')
except Exception as e:
    print(e, file=sys.stderr)
    sys.exit(1)
")
  read -r CLIENT_ID CLIENT_SECRET SECRET_HASH <<< "${CRED_OUTPUT}"

  # タイムスタンプ
  CREATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  aws dynamodb put-item \
    --table-name "${AUTH_TABLE}" \
    --item "{
      \"client_id\":     {\"S\": \"${CLIENT_ID}\"},
      \"company_id\":    {\"N\": \"${AUTH_COMPANY_ID}\"},
      \"secret_hash\":   {\"S\": \"${SECRET_HASH}\"},
      \"is_active\":     {\"N\": \"1\"},
      \"created_at\":    {\"S\": \"${CREATED_AT}\"}
    }" \
    --endpoint-url "${ENDPOINT}" --region "${REGION}"

  echo "[init] 認証クライアントの初期データを投入しました。"
  
  # ファイル書き出し
  OUTPUT_FILE="/output/test_credential.txt"
  {
      echo "client_id=${CLIENT_ID}"
      echo "client_secret=${CLIENT_SECRET}"
  } > "${OUTPUT_FILE}"

  echo "[init] 認証情報をlocal_data/dynamodb_init/test_credential.txtに保存しました"
fi

echo "[init] 完了しました。"
