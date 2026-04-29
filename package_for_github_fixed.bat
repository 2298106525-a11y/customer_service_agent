@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo ZhiNeng KeFu XiTong - GitHub DaBao ZhuShou
echo ========================================
echo.

REM Check src directory and files
echo [Check] Verifying project files...
if exist "src\new_agent.py" (
    echo [OK] src\new_agent.py exists
) else (
    echo [ERROR] Missing src\new_agent.py
    echo.
    echo Please complete the following steps:
    echo 1. Main program file should be at src\new_agent.py
    echo 2. If file is in root directory, run: move new_agent.py src\
    pause
    exit /b 1
)

if not exist "README.md" (
    echo [WARNING] Missing README.md
)

if not exist "requirements.txt" (
    echo [WARNING] Missing requirements.txt
)

if not exist ".gitignore" (
    echo [WARNING] Missing .gitignore
)

echo.
echo [Check] Git status...
if exist ".git" (
    echo [OK] Git repository initialized
    echo.
    git status
    echo.
    set /p confirm="Continue to commit? (Y/N): "
    if /i not "%confirm%"=="Y" (
        echo Operation cancelled
        pause
        exit /b 0
    )
) else (
    echo [INFO] Git repository not found, initializing...
    where git >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Git not installed!
        echo.
        echo Please install Git first: https://git-scm.com/download/win
        echo Or use GitHub Desktop
        pause
        exit /b 1
    )
    
    git init
    if errorlevel 1 (
        echo [ERROR] Git initialization failed
        pause
        exit /b 1
    )
    echo [OK] Git repository created successfully
)

echo.
echo [Execute] Adding files to Git...
git add .

echo.
echo [Execute] Creating commit...
git commit -m "Initial commit: Intelligent Customer Service System"

echo.
echo ========================================
echo Packaging completed!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Create a new repository on GitHub (do NOT check Initialize with README)
echo 2. Copy repository URL, then run:
echo.
echo    git remote add origin https://github.com/USERNAME/REPO.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo Or use GitHub Desktop to push directly
echo.
echo Tip: Check UPLOAD_TO_GITHUB.md for detailed guide
echo ========================================
pause
