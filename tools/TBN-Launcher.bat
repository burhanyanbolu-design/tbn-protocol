@echo off
title Hardin AI Solutions — Control Panel
color 0A
cls

echo.
echo  =====================================================
echo    HARDIN AI SOLUTIONS — Control Panel
echo    Burhan Yanbolu
echo  =====================================================
echo.
echo  Opening all services...
echo.

:: ── 1. TBN PROTOCOL (Main Product) ──────────────────
echo  [TBN Protocol]
echo    Dashboard      : https://tbn.hardinai.co.uk
echo    Governance     : https://tbn.hardinai.co.uk/governance
echo    Certification  : https://tbn.hardinai.co.uk/certification
echo    Pricing        : https://tbn.hardinai.co.uk/pricing
echo    Demo           : https://tbn.hardinai.co.uk/demo
echo.

:: ── 2. HARDIN AI MAIN SITE ───────────────────────────
echo  [Hardin AI]
echo    Main Site      : https://hardinai.co.uk
echo    AI Service     : https://ai.hardinai.co.uk
echo    Blog           : https://blog.hardinai.co.uk
echo.

:: ── 3. OTHER SERVICES ────────────────────────────────
echo  [Other Services]
echo    LGMD Agent     : https://lgmd.hardinai.co.uk
echo    Video CV       : https://video-cv.hardinai.co.uk
echo.

:: ── 4. DEVELOPER LINKS ───────────────────────────────
echo  [Developer]
echo    GitHub         : https://github.com/burhanyanbolu-design/tbn-protocol
echo    PyPI Package   : https://pypi.org/project/tbn-protocol/0.1.0/
echo    YC Demo Video  : https://drive.google.com/file/d/1SfLMFRSgrhx1lHDQc-pKDOCtI5LsH3Y8/view
echo.

echo  =====================================================
echo.
echo  Choose what to open:
echo.
echo    [1] Open ALL links in browser
echo    [2] TBN Protocol only
echo    [3] Hardin AI main site only
echo    [4] Start LOCAL dev server (for coding)
echo    [5] Open GitHub repo
echo    [6] Exit
echo.
set /p choice="  Enter number: "

if "%choice%"=="1" goto OPEN_ALL
if "%choice%"=="2" goto OPEN_TBN
if "%choice%"=="3" goto OPEN_HARDIN
if "%choice%"=="4" goto START_LOCAL
if "%choice%"=="5" goto OPEN_GITHUB
if "%choice%"=="6" exit
goto END

:OPEN_ALL
echo.
echo  Opening all services in browser...
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk/governance"
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk/certification"
timeout /t 1 /nobreak >nul
start "" "https://hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://ai.hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://blog.hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://lgmd.hardinai.co.uk"
echo  Done! All links opened.
goto END

:OPEN_TBN
echo.
echo  Opening TBN Protocol...
start "" "https://tbn.hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk/governance"
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk/certification"
timeout /t 1 /nobreak >nul
start "" "https://tbn.hardinai.co.uk/pricing"
goto END

:OPEN_HARDIN
echo.
echo  Opening Hardin AI...
start "" "https://hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://ai.hardinai.co.uk"
timeout /t 1 /nobreak >nul
start "" "https://blog.hardinai.co.uk"
goto END

:START_LOCAL
echo.
echo  Starting local dev server...
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
echo  Server starting at http://localhost:5000
timeout /t 2 /nobreak >nul
start "" "http://localhost:5000"
python server.py
goto END

:OPEN_GITHUB
start "" "https://github.com/burhanyanbolu-design/tbn-protocol"
goto END

:END
echo.
pause
