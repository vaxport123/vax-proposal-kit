@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title VAXPORT 제안 키트 설치

echo.
echo  ============================================================
echo   VAXPORT 제안 키트(vax-proposal-kit) 설치 — 더블클릭 설치기
echo   스킬 → %%USERPROFILE%%\.claude\skills   글꼴 → 사용자 글꼴 폴더
echo   관리자 권한 필요 없음. 다시 실행하면 최신으로 덮어씁니다.
echo  ============================================================
echo.

rem ── 1. 저장소 위치 — 이 파일이 저장소 안에 있으면 그대로, 혼자 내려받은 것이면 홈 폴더에 받는다
set "DIR=%~dp0"
if not exist "%DIR%install.sh" (
  set "DIR=%USERPROFILE%\vax-proposal-kit\"
  where git >nul 2>&1
  if errorlevel 1 (
    echo  [X] Git이 없습니다. Git for Windows를 먼저 설치한 뒤 이 파일을 다시 실행하세요.
    echo      설치 화면을 엽니다: https://git-scm.com/download/win  ^(기본값으로 다음-다음-설치^)
    start https://git-scm.com/download/win
    pause & exit /b 1
  )
  if exist "!DIR!.git" (
    echo  [·] 저장소 최신으로 당기기: !DIR!
    git -C "!DIR!" pull --ff-only
  ) else (
    echo  [·] 저장소 받기: !DIR!
    git clone https://github.com/vaxport123/vax-proposal-kit "!DIR!" || (echo  [X] 받기 실패 — 인터넷·권한 확인 & pause & exit /b 1)
  )
)

rem ── 2. Git Bash 찾기 — install.sh 는 bash 스크립트다 (WSL bash 가 아니라 Git 에 딸린 bash)
set "BASH="
for %%p in ("%ProgramFiles%\Git\bin\bash.exe" "%ProgramFiles(x86)%\Git\bin\bash.exe" "%LocalAppData%\Programs\Git\bin\bash.exe") do (
  if not defined BASH if exist "%%~p" set "BASH=%%~p"
)
if not defined BASH (
  for /f "delims=" %%g in ('where git 2^>nul') do (
    if not defined BASH if exist "%%~dpg..\bin\bash.exe" set "BASH=%%~dpg..\bin\bash.exe"
    if not defined BASH if exist "%%~dpg..\..\bin\bash.exe" set "BASH=%%~dpg..\..\bin\bash.exe"
  )
)
if not defined BASH (
  echo  [X] Git Bash 를 찾지 못했습니다. Git for Windows 를 설치하면 함께 들어옵니다.
  start https://git-scm.com/download/win
  pause & exit /b 1
)

rem ── 3. 파이썬 — 없어도 설치는 되지만 점검·렌더가 안 돈다
where python >nul 2>&1
if errorlevel 1 (
  echo  [!] 파이썬이 없습니다. 3.10 이상을 설치하면 준비 점검·HTML 렌더가 됩니다 ^(설치 때 "Add to PATH" 체크^).
  echo      https://www.python.org/downloads/windows/
)

rem ── 4. 나는 누구 — 노션 「제안 방식 — 이름」 페이지를 찾는 열쇠. 로그인 계정이 아니라 이 이름으로 찾는다
if exist "%USERPROFILE%\.vax-proposal\me.json" (
  echo  [·] 담당자 이름은 이미 있습니다: %USERPROFILE%\.vax-proposal\me.json  ^(바꾸려면 Claude 에게 「나는 ○○」^)
  set "NAME="
) else (
  set /p "NAME= 이 PC에서 제안서 쓰는 사람 이름 (노션 「제안 방식 — 이름」과 같게, 비우면 첫 작업 때 Claude 가 묻습니다): "
)

rem ── 5. 설치 — --force 로 스킬·에이전트·명령·글꼴을 최신으로 덮어쓴다 (me.json 은 지우지 않는다)
echo.
if defined NAME (
  "%BASH%" "%DIR%install.sh" --force --me "!NAME!"
) else (
  "%BASH%" "%DIR%install.sh" --force --me ""
)
set "RC=%errorlevel%"

echo.
if not "%RC%"=="0" (
  echo  [X] 설치가 중간에 멈췄습니다 ^(코드 %RC%^). 위 메시지를 그대로 Claude 에게 붙여 주면 이어서 처리합니다.
) else (
  echo  ============================================================
  echo   설치 끝. 이제 Claude Code 를 열고 이렇게 말하세요:
  echo     「준비 점검」                          → 커넥터·글꼴 등 빠진 것을 Claude 가 확인·요구
  echo     「{제안서명} A4 횡 제안」               → 제안서 시작 ^(예: ○○대학교 VR 실습실 구축 A4 횡 제안^)
  echo     「방식 저장: …」 「방식 불러와」         → 노션 나만의 방식 저장·불러오기
  echo   저장소 폴더: !DIR!
  echo  ============================================================
)
echo.
pause
endlocal
