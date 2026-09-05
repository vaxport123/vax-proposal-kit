#!/usr/bin/env bash
# vax-proposal-kit 원클릭 설치 (직원 PC용)
# 사용: bash install.sh            (승인 스킬 전체 설치 + 글꼴 Freesentation·Paperlogy 설치)
#       bash install.sh --force    (기존 설치 덮어쓰기)
#       bash install.sh --list     (매니페스트만 출력)
#       bash install.sh --no-fonts (글꼴 설치 생략)
#
# 원리: skills.tsv(=승인 스킬의 정본)를 읽어 각 스킬을 내 에이전트 환경(~/.claude/skills,
#       ~/.codex/skills)에 설치한다. vax-wiki-gateway/skills/install.sh 와 같은 방식이다.
set -euo pipefail

FORCE=0; LIST_ONLY=0; FONTS=1
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    --list)  LIST_ONLY=1 ;;
    --no-fonts) FONTS=0 ;;
    *) echo "알 수 없는 옵션: $a"; exit 2 ;;
  esac
done

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$DIR/skills.tsv"
[ -f "$MANIFEST" ] || { echo "매니페스트 없음: $MANIFEST"; exit 1; }

CLAUDE_DIR="$HOME/.claude/skills"
CODEX_DIR="$HOME/.codex/skills"
HAS_CLAUDE=0; HAS_CODEX=0
[ -d "$HOME/.claude" ] && HAS_CLAUDE=1
[ -d "$HOME/.codex" ]  && HAS_CODEX=1

log(){ printf '  %s\n' "$*"; }
hdr(){ printf '\n▶ %s\n' "$*"; }

# 스킬 레포에서 SKILL.md가 든 디렉터리를 찾아 대상 스킬 폴더로 복사
copy_skill_dir(){ # $1=repo_root  $2=dest_name
  local repo="$1" name="$2" src
  # 이름이 같은 폴더(skills/<name>/SKILL.md 등)를 먼저 고른다. vax-wiki-gateway처럼 SKILL.md가 여럿인 저장소에서 첫 것을 집으면 딴 스킬이 그 이름으로 깔린다(2026-09-05 리뷰).
  src="$(dirname "$(find "$repo" -path "*/$name/SKILL.md" -not -path '*/node_modules/*' -not -path '*/.tmp*' | head -n1)")" || true
  if [ -z "${src:-}" ] || [ "$src" = "." ] || [ ! -d "$src" ]; then
    src="$(dirname "$(find "$repo" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/.tmp*' -not -path '*/.claude/*' | head -n1)")" || true
  fi
  if [ -z "${src:-}" ] || [ ! -d "$src" ]; then
    log "⚠ SKILL.md를 못 찾음 — 수동 확인 필요: $repo"; return 1
  fi
  # 콜론으로 묶어 풀던 방식은 set -u 에서 "rest: unbound variable"로 죽었다(2026-09-04 실측 — 첫 설치가 여기서 멈춤).
  # 경로에 콜론이 들어갈 수도 있어(Windows) 묶지 않고 키별로 고른다.
  local key base ok dest
  for key in claude codex; do
    case ",$TARGETS," in *",$key,"*) : ;; *) continue ;; esac
    if [ "$key" = claude ]; then base="$CLAUDE_DIR"; ok="$HAS_CLAUDE"; else base="$CODEX_DIR"; ok="$HAS_CODEX"; fi
    [ "$ok" = 1 ] || { log "· $key 환경 없음 → 건너뜀"; continue; }
    dest="$base/$name"
    if [ -d "$dest" ] && [ "$FORCE" = 0 ]; then log "· 이미 설치됨(스킵): $dest"; continue; fi
    mkdir -p "$base"; rm -rf "$dest"; cp -R "$src" "$dest"
    log "✓ 설치: $dest"
  done
}

install_git(){ # $1=name $2=source
  local name="$1" source="$2" tmp
  # 이 저장소 자신(vax-proposal)은 clone 없이 로컬에서 바로 복사한다
  if [ "$name" = "vax-proposal" ]; then copy_skill_dir "$DIR/skills/vax-proposal" "$name"; return; fi
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' RETURN
  log "clone $source"
  git clone --depth 1 "$source" "$tmp/repo" >/dev/null 2>&1 || { log "⚠ clone 실패"; return 1; }
  copy_skill_dir "$tmp/repo" "$name"
  [ -f "$tmp/repo/requirements.txt" ] && { log "pip 의존성 설치"; python3 -m pip install -q -r "$tmp/repo/requirements.txt" || log "⚠ pip 실패 — 수동 설치"; }
  [ "$name" = "deep-research" ] && { python3 -m pip install -q pyyaml 2>/dev/null || true; }
}

install_npx(){ # $1=name $2=source
  command -v npx >/dev/null 2>&1 || { log "⚠ npx 없음 — Node 설치 후 재시도"; return 1; }
  log "npx skills add $2"
  # npx skills add 는 **현재 폴더**의 .claude/skills·.agents/skills 에 떨군다. 저장소 안에서 돌리면 저장소가 오염된다
  # (2026-09-04 실측 — humanizer 가 저장소에 커밋될 뻔했다). 홈에서 돌려 ~/.claude/skills 에 들어가게 한다.
  ( cd "$HOME" && npx -y skills add "$2" >/dev/null 2>&1 ) && log "✓ 설치: $1 → ~/.claude/skills" || log "⚠ 실패 — 수동: cd ~ && npx skills add $2"
}

install_marketplace(){ # $1=name $2=source $3=note
  log "ⓘ Claude Code 안에서 1회 실행(스크립트로는 못 깐다):"
  case "$1" in
    fluent-korean)   log "   /plugin marketplace add snflkd/fluent-korean"; log "   /plugin install fluent-korean@fluent-korean"; log "   → /config 에서 output-style 을 fluent-korean 으로" ;;
    humanize-korean) log "   /plugin marketplace add epoko77-ai/im-not-ai"; log "   /plugin install humanize-korean@im-not-ai" ;;
    *)               log "   Claude Code > Customize > Add from marketplace → $2 → Sync" ;;
  esac
}

install_builtin(){ # $1=name
  log "ⓘ 내장 — 설치 불필요(데스크톱 Claude에 이미 있음): $1"
}

install_mcp(){ # $1=name $2=source(owner/repo@version) — MCP 서버는 Claude Code CLI에 등록한다. 판을 고정한다(npx -y pkg@version).
  local name="$1" src="$2" pkg
  pkg="${src##*/}"
  if ! command -v claude >/dev/null 2>&1; then log "ⓘ claude CLI 없음 — 데스크톱 Claude는 설정 > 커넥터에서 MCP 추가: npx -y $pkg"; return 0; fi
  if claude mcp list 2>/dev/null | grep -q "^$name"; then log "· 이미 등록됨(스킵): $name"; return 0; fi
  claude mcp add "$name" -- npx -y "$pkg" >/dev/null 2>&1 && log "✓ 등록: claude mcp add $name -- npx -y $pkg" || log "⚠ 실패 — 수동: claude mcp add $name -- npx -y $pkg"
}

[ "$LIST_ONLY" = 0 ] && hdr "vax-proposal-kit 설치 시작  (claude=$HAS_CLAUDE, codex=$HAS_CODEX, force=$FORCE)"

while IFS=$'\t' read -r name method source TARGETS note; do
  case "$name" in ''|\#*) continue ;; esac
  name="$(echo "$name" | xargs)"; method="$(echo "$method" | xargs)"
  source="$(echo "$source" | xargs)"; TARGETS="$(echo "${TARGETS:-claude}" | xargs)"
  if [ "$LIST_ONLY" = 1 ]; then printf '  %-16s %-12s %s\n' "$name" "$method" "$source"; continue; fi
  hdr "$name  ($method)"
  case "$method" in
    git)         install_git "$name" "$source" ;;
    npx)         install_npx "$name" "$source" ;;
    marketplace) install_marketplace "$name" "$source" "${note:-}" ;;
    builtin)     install_builtin "$name" ;;
    mcp)         install_mcp "$name" "$source" ;;
    *) log "⚠ 알 수 없는 method: $method" ;;
  esac
done < "$MANIFEST"

if [ "$LIST_ONLY" = 1 ]; then
  printf '  %-16s %-12s %s\n' "fonts" "local" "fonts/ (Freesentation·Paperlogy 18종, SIL OFL) → 사용자 글꼴 폴더"
  exit 0
fi

# 에이전트 — agents/*.md 를 ~/.claude/agents/ 로 복사한다(비판자 proposal-critic 등). 서브에이전트는 이 폴더에서만 읽힌다.
if [ "$HAS_CLAUDE" = 1 ] && ls "$DIR"/agents/*.md >/dev/null 2>&1; then
  hdr "agents  (~/.claude/agents)"
  mkdir -p "$HOME/.claude/agents"
  for f in "$DIR"/agents/*.md; do
    b="$(basename "$f")"; [ "$b" = "README.md" ] && continue
    if [ -f "$HOME/.claude/agents/$b" ] && [ "$FORCE" = 0 ]; then log "· 이미 있음(스킵): $b"; continue; fi
    cp "$f" "$HOME/.claude/agents/$b"; log "✓ 설치: ~/.claude/agents/$b"
  done
fi

# /bid-loop 명령 — loops/bid-loop/bid-loop.md 를 ~/.claude/commands/ 로 복사한다(이게 없으면 SKILL.md가 말하는 「/bid-loop 사업폴더」가 없는 명령이다 · 2026-09-05 리뷰).
if [ "$HAS_CLAUDE" = 1 ] && [ -f "$DIR/loops/bid-loop/bid-loop.md" ]; then
  hdr "commands  (~/.claude/commands/bid-loop.md)"
  mkdir -p "$HOME/.claude/commands"
  if [ -f "$HOME/.claude/commands/bid-loop.md" ] && [ "$FORCE" = 0 ]; then log "· 이미 있음(스킵): bid-loop.md"
  else cp "$DIR/loops/bid-loop/bid-loop.md" "$HOME/.claude/commands/bid-loop.md"; log "✓ 설치: ~/.claude/commands/bid-loop.md"; fi
fi

# 글꼴 — 제안 슬라이드는 Freesentation(기본)·Paperlogy(표시용)를 쓴다(references/deck.md §4).
# 사용자 계정에만 설치하므로 관리자 권한이 필요 없다. 자세한 것은 fonts/README.md.
if [ "$FONTS" = 1 ] && [ -f "$DIR/fonts/install-fonts.sh" ]; then
  hdr "fonts  (Freesentation · Paperlogy)"
  if [ "$FORCE" = 1 ]; then bash "$DIR/fonts/install-fonts.sh" --force || log "⚠ 글꼴 설치 실패 — 수동: bash fonts/install-fonts.sh"
  else bash "$DIR/fonts/install-fonts.sh" || log "⚠ 글꼴 설치 실패 — 수동: bash fonts/install-fonts.sh"; fi
fi

hdr "완료. marketplace 항목은 위 ⓘ 안내대로 Claude Code 에서 1회 실행하세요."
