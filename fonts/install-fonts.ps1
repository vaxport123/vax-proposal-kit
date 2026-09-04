# vax-proposal-kit 글꼴 설치 (Windows · 현재 사용자 · 관리자 권한 불필요)
# 사용: powershell -ExecutionPolicy Bypass -File fonts\install-fonts.ps1 [-Force]
# 원리: 사용자 글꼴 폴더(%LOCALAPPDATA%\Microsoft\Windows\Fonts)에 TTF를 복사하고
#       HKCU\...\Fonts 레지스트리에 등록한다(Windows 10 1809+ 의 사용자 단위 글꼴 설치 방식).
#       Figma 데스크톱·PowerPoint·브라우저가 재시작 후 바로 인식한다.
param([switch]$Force)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$reg  = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
if (-not (Test-Path $reg)) { New-Item -Path $reg -Force | Out-Null }

# 파일명 → 레지스트리 표시 이름. "Freesentation-7Bold.ttf" → "Freesentation 7 Bold (TrueType)"
function DisplayName([string]$file) {
    $base = [IO.Path]::GetFileNameWithoutExtension($file)          # Freesentation-7Bold
    $parts = $base -split "-", 2
    $family = $parts[0]
    $weight = if ($parts.Count -gt 1) { $parts[1] } else { "Regular" }
    $weight = ($weight -replace "^(\d)", '$1 ') -replace "([a-z])([A-Z])", '$1 $2'   # 7Bold → 7 Bold, ExtraBold → Extra Bold
    return "$family $weight (TrueType)"
}

$installed = 0; $skipped = 0
Get-ChildItem -Path $root -Recurse -Filter *.ttf | ForEach-Object {
    $target = Join-Path $dest $_.Name
    $name = DisplayName $_.Name
    $registered = (Get-ItemProperty -Path $reg -Name $name -ErrorAction SilentlyContinue) -ne $null
    if ((Test-Path $target) -and -not $Force) {
        # 파일이 이미 있으면 설치된 것으로 본다(다른 이름으로 등록돼 있을 수 있다). 우리 이름의 등록만 보완한다.
        if (-not $registered) { New-ItemProperty -Path $reg -Name $name -Value $target -PropertyType String -Force | Out-Null }
        $skipped++; return
    }
    try {
        Copy-Item -Path $_.FullName -Destination $target -Force -ErrorAction Stop
    } catch [System.IO.IOException] {
        # 글꼴을 어떤 앱(Figma·PowerPoint·브라우저)이 쓰는 중이면 덮어쓸 수 없다. 이미 같은 글꼴이므로 건너뛴다.
        Write-Host ("  · 사용 중이라 덮어쓰지 못함(이미 설치됨): {0}" -f $_.Name); $skipped++; return
    }
    New-ItemProperty -Path $reg -Name $name -Value $target -PropertyType String -Force | Out-Null
    $installed++
}
Write-Host ("  글꼴 설치 {0}개 · 이미 있음 {1}개 → {2}" -f $installed, $skipped, $dest)
if ($installed -gt 0) { Write-Host "  ※ Figma·PowerPoint·브라우저를 다시 열면 Freesentation·Paperlogy 가 보입니다." }
