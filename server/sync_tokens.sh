#!/usr/bin/env bash
# 서버 ops/ui_tokens.py (정본) → 스킬 사본 동기화. 반대 방향으로는 절대 하지 않는다.
# 사용: SSH_TARGET=<user@host> bash server/sync_tokens.sh
#   SSH_TARGET 은 환경변수로만 받는다 — 서버 주소를 저장소에 적지 않는다(공개 금지 규칙).
set -euo pipefail
: "${SSH_TARGET:?SSH_TARGET=<user@host> 를 주세요 (주소는 저장소에 적지 않는다)}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$DIR/skills/vax-proposal/scripts/ui_tokens.py"
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT

scp -q "$SSH_TARGET:/opt/vax/ops/ui_tokens.py" "$TMP"
# 첫 줄(shebang) 아래에 사본 표시를 끼운다
{
  head -n1 "$TMP"
  printf '# ⚠️ 이 파일은 서버 `ops/ui_tokens.py`의 **사본**이다. 색·간격을 고칠 일이 있으면 서버 정본을 고치고\n'
  printf '#    `server/sync_tokens.sh`로 여기로 옮긴다(반대로 하지 않는다). %s 동기화.\n' "$(date +%F)"
  tail -n +2 "$TMP"
} > "$DST"

python3 "$DST" --selftest
echo "동기화 완료: $DST"
