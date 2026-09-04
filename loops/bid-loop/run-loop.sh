#!/usr/bin/env bash
# run-loop.sh — /bid-loop 야간 실행 래퍼
# cron 이 이 스크립트를 매시 정각에 부른다. 시간대·중복실행·예산·로그를 여기서 통제한다.
#
#   crontab -e
#   0 * * * * /Users/vax/bids-project/run-loop.sh 몽골유적
#
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo /usr/local/bin/claude)}"
TARGET="${1:-}"

MAX_BUDGET_USD="${MAX_BUDGET_USD:-3}"   # 1스텝 상한. 초과 시 프로세스가 스스로 종료
MAX_TURNS="${MAX_TURNS:-60}"
TIMEOUT_SEC="${TIMEOUT_SEC:-1800}"      # 30분

cd "$PROJECT_DIR" || exit 1
mkdir -p logs
LOG="logs/loop-$(date +%Y%m%d).log"
say(){ echo "[$(date '+%F %T')] $*" >> "$LOG"; }

# ── 1. 작업 시간대: 21:00~08:59 만 허용 ──────────────────────────────
H=$(date +%H); H=${H#0}; H=${H:-0}
if (( H < 21 && H > 8 )); then
  exit 0                                  # 조용히 종료. 로그도 남기지 않는다
fi

# ── 2. 중복 실행 차단 ────────────────────────────────────────────────
LOCK="logs/.loop.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  say "SKIP 이전 실행이 아직 돌고 있음 ($LOCK)"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# ── 3. 이미 끝난 사업이면 실행하지 않는다 ────────────────────────────
STATE="bids/${TARGET}/_STATE.md"
if [[ -n "$TARGET" && -f "$STATE" ]]; then
  if grep -qE '^\s*상태:\s*(완료|중단)' "$STATE"; then
    say "STOP $TARGET 종료 상태 — $(grep -E '^\s*상태:' "$STATE" | head -1 | tr -s ' ')"
    exit 0
  fi
fi

# ── 4. 헤드리스 1스텝 실행 ───────────────────────────────────────────
say "RUN  /bid-loop ${TARGET:-(현황조회)}"

timeout "$TIMEOUT_SEC" "$CLAUDE_BIN" -p "/bid-loop ${TARGET}" \
  --permission-mode acceptEdits \
  --max-turns "$MAX_TURNS" \
  --max-budget-usd "$MAX_BUDGET_USD" \
  --output-format json \
  >> "logs/result-$(date +%Y%m%d-%H%M).json" 2>> "$LOG"

RC=$?
case $RC in
  0)   say "DONE 정상 종료" ;;
  124) say "TIMEOUT ${TIMEOUT_SEC}s 초과 — 다음 정각에 재시도. _STATE.md 진행중 플래그 확인" ;;
  *)   say "FAIL 종료코드 $RC (사용량 한도·예산 상한·오류 가능) — 다음 정각에 재시도" ;;
esac

# 실패해도 아무것도 되돌리지 않는다.
# 재시작은 cron 이 담당하고, 재개 지점은 _STATE.md 가 담당한다.
exit 0
