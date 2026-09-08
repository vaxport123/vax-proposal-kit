#!/bin/bash
# macOS 더블클릭 설치기 — Finder에서 두 번 누르면 터미널이 열리고 install.sh --force 가 돈다.
# 처음 한 번 「열 수 없음」이 뜨면: 파일 우클릭 → 열기, 또는 시스템 설정 → 개인정보 보호 → 「그래도 열기」.
cd "$(dirname "$0")" || exit 1
echo "VAXPORT 제안 키트 설치 — $(pwd)"
if [ -f "$HOME/.vax-proposal/me.json" ]; then
  echo "담당자 이름은 이미 있습니다: $HOME/.vax-proposal/me.json (바꾸려면 Claude에게 「나는 ○○」)"
  bash install.sh --force --me ""
else
  bash install.sh --force
fi
echo
echo "설치 끝. Claude Code에서 「준비 점검」 → 「{제안서명} A4 횡 제안」 으로 시작하세요."
read -r -p "아무 키나 누르면 닫힙니다 " _
