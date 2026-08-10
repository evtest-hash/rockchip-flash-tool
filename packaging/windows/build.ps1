param(
    [string]$AppName = "Rockchip Flash Tool",
    [string]$ZipName = "Rockchip-Flash-Tool-windows-x64.zip",
    [string]$VenvDir = ".venv-win",
    [string]$PythonExe = "python",
    [string]$IconPng = "assets/icon-1024.png",
    [string]$IconIco = "assets/icon.ico"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) | Resolve-Path
Set-Location $root

if (-not (Test-Path $VenvDir)) {
    & $PythonExe -m venv $VenvDir
}

$venvPython = Join-Path $VenvDir "Scripts/python.exe"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install --no-compile -r requirements.txt pyinstaller

if (-not (Test-Path $IconPng)) {
    throw "Icon source not found: $IconPng"
}

$needRebuildIcon = (-not (Test-Path $IconIco)) -or ((Get-Item $IconPng).LastWriteTimeUtc -gt (Get-Item $IconIco).LastWriteTimeUtc)
if ($needRebuildIcon) {
    & $venvPython packaging/icons/make_ico.py $IconPng $IconIco
}

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "$AppName" `
    --icon "$IconIco" `
    --add-data "$IconIco;assets" `
    --add-data "vendor/upgrade_tool/windows;vendor/upgrade_tool/windows" `
    --add-data "vendor/rkbin;vendor/rkbin" `
    rk_flash_tool/__main__.py

$zipPath = Join-Path "dist" $ZipName
if (Test-Path $zipPath) {
    Remove-Item -Recurse -Force $zipPath
}

Compress-Archive -Path "dist/$AppName/*" -DestinationPath $zipPath -Force
Write-Host "Done: $zipPath"
