#!/usr/bin/env bash
# vax-proposal-kit 글꼴 설치 — Freesentation · Paperlogy (SIL OFL 1.1, 재배포 허용)
# 사용: bash fonts/install-fonts.sh [--force]
#   Windows(Git Bash) → install-fonts.ps1 로 넘긴다(사용자 글꼴 폴더 + HKCU 레지스트리)
#   macOS            → ~/Library/Fonts
#   Linux            → ~/.local/share/fonts + fc-cache
set -euo pipefail
FORCE=0; [ "${1:-}" = "--force" ] && FORCE=1
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    PS1_PATH="$(cygpath -w "$DIR/install-fonts.ps1" 2>/dev/null || echo "$DIR/install-fonts.ps1")"
    if [ "$FORCE" = 1 ]; then
      powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_PATH" -Force
    else
      powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_PATH"
    fi
    ;;
  Darwin)
    dest="$HOME/Library/Fonts"; mkdir -p "$dest"; n=0; s=0
    for f in "$DIR"/*/*.ttf; do
      if [ -f "$dest/$(basename "$f")" ] && [ "$FORCE" = 0 ]; then s=$((s+1)); continue; fi
      cp "$f" "$dest/"; n=$((n+1))
    done
    echo "  글꼴 설치 ${n}개 · 이미 있음 ${s}개 → $dest (앱을 다시 열면 보입니다)"
    ;;
  *)
    dest="$HOME/.local/share/fonts/vax-proposal-kit"; mkdir -p "$dest"; n=0; s=0
    for f in "$DIR"/*/*.ttf; do
      if [ -f "$dest/$(basename "$f")" ] && [ "$FORCE" = 0 ]; then s=$((s+1)); continue; fi
      cp "$f" "$dest/"; n=$((n+1))
    done
    command -v fc-cache >/dev/null 2>&1 && fc-cache -f "$dest" >/dev/null 2>&1 || true
    echo "  글꼴 설치 ${n}개 · 이미 있음 ${s}개 → $dest"
    ;;
esac
