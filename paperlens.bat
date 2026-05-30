@echo off
:: ──────────────────────────────────────────────────────────────
::  PaperLens bootstrap launcher (Windows / cmd / PowerShell)
::
::  Tujuan:
::    Setelah `git clone`, user cukup ketik:
::        paperlens setup
::        paperlens dev
::    tanpa perlu install Python, uv, atau virtualenv terlebih dahulu.
::
::  Logika:
::    1. Pastikan `uv` ada (auto-install via PowerShell kalau tidak).
::    2. Pastikan dependency Python ter-sync (uv sync kalau pertama kali).
::    3. Forward semua argumen ke `uv run paperlens <args>`.
::
::  Path: file ini di-resolve relatif ke direktorinya sendiri (%~dp0),
::  jadi user bisa panggil dari subfolder.
:: ──────────────────────────────────────────────────────────────

setlocal ENABLEDELAYEDEXPANSION
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ── 1. Cek uv ───────────────────────────────────────────────
where uv >nul 2>&1
if errorlevel 1 (
    echo [paperlens] uv tidak ditemukan di PATH.
    echo [paperlens] Mencoba install uv via PowerShell...
    powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo [paperlens] Auto-install uv gagal. Install manual:
        echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
        exit /b 1
    )
    :: Refresh PATH supaya uv terlihat di session ini
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    where uv >nul 2>&1
    if errorlevel 1 (
        echo [paperlens] uv masih belum ada di PATH. Restart terminal lalu jalankan ulang.
        exit /b 1
    )
)

:: ── 2. Cek apakah deps Python sudah ter-sync ────────────────
if not exist "%ROOT%\.venv" (
    echo [paperlens] First run — installing Python dependencies...
    pushd "%ROOT%"
    uv sync --extra frontend --extra dev
    set "SYNC_RC=!errorlevel!"
    popd
    if !SYNC_RC! neq 0 (
        echo [paperlens] uv sync gagal ^(exit !SYNC_RC!^).
        exit /b !SYNC_RC!
    )
)

:: ── 3. Forward ke CLI ───────────────────────────────────────
pushd "%ROOT%"
uv run paperlens %*
set "RC=%errorlevel%"
popd
exit /b %RC%
