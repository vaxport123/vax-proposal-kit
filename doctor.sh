#!/usr/bin/env bash
# vax-proposal-kit 설치 점검 — "왜 안 되죠"를 줄인다 (한준 2026-09-04 "체크 필요")
# 사용: bash doctor.sh
# 점검: 스킬 설치 · 글꼴 · python3 · 렌더러 셀프테스트 · 저장소 최신 여부. 커넥터(Notion·Figma)는 셸에서 볼 수 없어 확인 방법만 안내한다.
set -uo pipefail
export PYTHONIOENCODING=utf-8   # 한글 출력이 cp949 콘솔에서 죽지 않게
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ok(){ printf '  ✓ %s\n' "$*"; }
bad(){ printf '  ✗ %s\n' "$*"; FAIL=$((FAIL+1)); }
info(){ printf '  ⓘ %s\n' "$*"; }
FAIL=0

printf '\n▶ 스킬\n'
if [ -f "$HOME/.claude/skills/vax-proposal/SKILL.md" ]; then
  if diff -q "$HOME/.claude/skills/vax-proposal/SKILL.md" "$DIR/skills/vax-proposal/SKILL.md" >/dev/null 2>&1; then ok "vax-proposal 설치됨 · 저장소와 같은 버전"
  else bad "vax-proposal 설치본이 저장소와 다르다 → bash install.sh --force"; fi
else bad "vax-proposal 미설치 → bash install.sh"; fi
[ -f "$HOME/.claude/agents/proposal-critic.md" ] && ok "비판자 proposal-critic 설치됨" || bad "비판자 proposal-critic 미설치 → bash install.sh --force"
[ -f "$HOME/.claude/commands/bid-loop.md" ] && ok "/bid-loop 명령 설치됨" || info "/bid-loop 명령 없음(루프형만 필요) — bash install.sh --force"
for s in deep-research humanizer; do
  [ -d "$HOME/.claude/skills/$s" ] && ok "$s 설치됨" || info "$s 없음(선택) — install.sh 가 깐다"
done
for plug in fluent-korean humanize-korean; do
  if ls -d "$HOME/.claude/plugins"/*/*"$plug"* >/dev/null 2>&1 || grep -rqs "$plug" "$HOME/.claude/settings.json" 2>/dev/null; then ok "플러그인 $plug 흔적 있음"
  else info "플러그인 $plug 확인 안 됨 — Claude Code에서 /plugin install (install.sh 안내 참조)"; fi
done

printf '\n▶ 글꼴 (Freesentation · Paperlogy)\n'
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    n=$(ls "$LOCALAPPDATA/Microsoft/Windows/Fonts"/Freesentation-*.ttf "$LOCALAPPDATA/Microsoft/Windows/Fonts"/Paperlogy-*.ttf 2>/dev/null | wc -l | tr -d ' ') ;;
  Darwin) n=$(ls "$HOME/Library/Fonts"/Freesentation-*.ttf "$HOME/Library/Fonts"/Paperlogy-*.ttf 2>/dev/null | wc -l | tr -d ' ') ;;
  *)      n=$(ls "$HOME/.local/share/fonts/vax-proposal-kit"/*.ttf 2>/dev/null | wc -l | tr -d ' ') ;;
esac
if [ "${n:-0}" -ge 18 ]; then ok "글꼴 18/18 설치됨 (앱을 다시 열어야 보인다)"; else bad "글꼴 ${n:-0}/18 → bash fonts/install-fonts.sh"; fi

printf '\n▶ 파이썬 · 렌더러\n'
PY=""; for c in python3 python; do command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }; done
if [ -n "$PY" ]; then
  ok "$($PY --version 2>&1)"
  if $PY "$DIR/skills/vax-proposal/scripts/ui_tokens.py" --selftest >/dev/null 2>&1; then ok "ui_tokens 셀프테스트 통과"; else bad "ui_tokens 셀프테스트 실패"; fi
  if $PY "$DIR/skills/vax-proposal/scripts/render_html.py" --selftest >/dev/null 2>&1; then ok "render_html 셀프테스트 통과"; else info "render_html --selftest 없음 또는 실패 — 렌더 1회로 확인"; fi
  if $PY "$DIR/skills/vax-proposal/scripts/figures_svg.py" --selftest >/dev/null 2>&1; then ok "figures_svg 셀프테스트 통과"; else bad "figures_svg 셀프테스트 실패"; fi
  if $PY "$DIR/skills/vax-proposal/scripts/proposal_lint.py" --selftest >/dev/null 2>&1; then ok "proposal_lint 셀프테스트 통과"; else bad "proposal_lint 셀프테스트 실패"; fi
  if $PY "$DIR/skills/vax-proposal/scripts/layout_wireframes.py" --selftest >/dev/null 2>&1; then ok "layouts.json 셀프테스트 통과(틀 14종)"; else bad "layouts.json 셀프테스트 실패"; fi
  if $PY "$DIR/skills/vax-proposal/scripts/probe_web.py" --selftest >/dev/null 2>&1; then ok "probe_web 셀프테스트 통과"; else bad "probe_web 셀프테스트 실패"; fi
  if $PY -c "import ddgs" >/dev/null 2>&1; then ok "ddgs(웹 검색) 있음"; else info "ddgs 없음 — pip install -r skills/vax-proposal/scripts/requirements.txt (probe_web.py 가 쓴다)"; fi
  EX="$DIR/examples/예시문화재단_실감콘텐츠"
  if $PY "$DIR/skills/vax-proposal/scripts/proposal_lint.py" "$EX/04_제안서_v1.md" >/dev/null 2>&1 && $PY "$DIR/skills/vax-proposal/scripts/proposal_lint.py" "$EX/07_슬라이드계획_v1.md" --plan >/dev/null 2>&1; then ok "examples/ 예시가 lint 통과(상 0)"; else bad "examples/ 예시가 lint에 걸린다 — 규칙과 예시가 어긋났다"; fi
else bad "python3 없음 — HTML 렌더 불가"; fi

printf '\n▶ 저장소\n'
if git -C "$DIR" rev-parse >/dev/null 2>&1; then
  git -C "$DIR" fetch -q origin 2>/dev/null || info "원격 확인 실패(오프라인?)"
  behind=$(git -C "$DIR" rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
  [ "$behind" = "0" ] && ok "최신(main)" || bad "원격보다 ${behind} 커밋 뒤 → git pull && bash install.sh --force"
else info "git 저장소 아님(zip으로 받았나) — 갱신은 다시 clone"; fi

printf '\n▶ 커넥터 (Claude 안에서 확인)\n'
info "Notion: Claude에 「재료 팩 R26BK… 열어줘」 → 입찰 레이더 공고 밑 「📦 제안 재료 팩」이 열리면 정상"
info "Figma: Claude에 「Figma whoami」 → 회사 계정(vaxport)으로 나오면 정상. 개인 계정이면 슬라이드 파일 권한이 없다"
info "글꼴이 Figma에 안 보이면: Figma 데스크톱 재시작 → 텍스트 글꼴 목록에서 Freesentation 검색"

printf '\n'
if [ "$FAIL" = 0 ]; then echo "모두 정상."; else echo "문제 ${FAIL}건 — 위 ✗ 항목을 처리한다."; fi
exit $FAIL
