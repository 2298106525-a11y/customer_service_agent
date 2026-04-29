@echo off
REM Git初始化脚本 (Windows)

echo ========================================
echo 初始化Git仓库
echo ========================================
echo.

REM 检查是否已初始化
if exist ".git" (
    echo [提示] Git仓库已存在
    echo.
    set /p confirm="是否重新初始化？(y/n): "
    if /i not "%confirm%"=="y" exit /b 0
    rmdir /s /q .git
)

REM 初始化Git
git init
echo [√] Git仓库初始化完成
echo.

REM 添加所有文件
git add .
echo [√] 文件已添加到暂存区
echo.

REM 首次提交
git commit -m "Initial commit: 智能客服工单自动处理系统"
echo [√] 首次提交完成
echo.

echo ========================================
echo 下一步操作：
echo ========================================
echo.
echo 1. 在GitHub上创建新仓库
echo 2. 运行以下命令关联远程仓库：
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo ========================================
pause
