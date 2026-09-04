#!/usr/bin/env bash
# vax-proposal-kit 원클릭 설치 (직원 PC용)
# 사용: bash install.sh            (승인 스킬 전체 설치)
#       bash install.sh --force    (기존 설치 덮어쓰기)
#       bash install.sh --list     (매니페스트만 출력)
#
# 원리: skills.tsv(=승인 스킬의 정본)를 읽어 각 스킬을 내 에이전트 환경(~/.claude/skills,
#       ~/.codex/skills)에 설치한다. vax-wiki-gateway/skills/install.sh 와 같은 방식이다.
set -euo pipefail

FORCE=0; LIST_ONLY=0
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    --list)  LIST_ONLY=1 ;;
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
  src="$(dirname "$(find "$repo" -name SKILL.md -not -path '*/node_modules/*' | head -n1)")" || true
  if [ -z "${src:-}" ] || [ ! -d "$src" ]; then
    log "⚠ SKILL.md를 못 찾음 — 수동 확인 필요: $repo"; return 1
  fi
  for pair in "claude:$CLAUDE_DIR:$HAS_CLAUDE" "codex:$CODEX_DIR:$HAS_CODEX"; do
    local key="${pair%%:*}" rest="${pair#*:}" base="${rest%%:*}" ok="${rest##*:}"
    case ",$TARGETS," in *",$key,"*) : ;; *) continue ;; esac
    [ "$ok" = 1 ] || { log "· $key 환경 없음 → 건너뜀"; continue; }
    local dest="$base/$name"
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
  npx -y skills add "$2" >/dev/null 2>&1 && log "✓ 설치: $1" || log "⚠ 실패 — 수동: npx skills add $2"
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
    *) log "⚠ 알 수 없는 method: $method" ;;
  esac
done < "$MANIFEST"

[ "$LIST_ONLY" = 1 ] && exit 0
hdr "완료. marketplace 항목은 위 ⓘ 안내대로 Claude Code 에서 1회 실행하세요."
