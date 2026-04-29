@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo 智能客服系统 - GitHub打包助手
echo ========================================
echo.

REM 检查src目录和文件
echo [检查] 验证项目文件...
if exist "src\new_agent.py" (
    echo [OK] src\new_agent.py 已存在
) else (
    echo [错误] 缺少 src\new_agent.py
    echo.
    echo 请确认您已完成以下步骤：
    echo 1. 主程序文件应该在 src\new_agent.py
    echo 2. 如果文件在根目录，请运行: move new_agent.py src\
    pause
    exit /b 1
)

if not exist "README.md" (
    echo [警告] 缺少 README.md
)

if not exist "requirements.txt" (
    echo [警告] 缺少 requirements.txt
)

if not exist ".gitignore" (
    echo [警告] 缺少 .gitignore
)

echo.
echo [检查] Git状态...
if exist ".git" (
    echo [OK] Git仓库已初始化
    echo.
    git status
    echo.
    set /p confirm="是否继续提交？(Y/N): "
    if /i not "%confirm%"=="Y" (
        echo 操作已取消
        pause
        exit /b 0
    )
) else (
    echo [信息] 未检测到Git仓库，正在初始化...
    where git >nul 2>&1
    if errorlevel 1 (
        echo [错误] Git未安装！
        echo.
        echo 请先安装Git: https://git-scm.com/download/win
        echo 或使用GitHub Desktop
        pause
        exit /b 1
    )
    
    git init
    if errorlevel 1 (
        echo [错误] Git初始化失败
        pause
        exit /b 1
    )
    echo [OK] Git仓库创建成功
)

echo.
echo [执行] 添加文件到Git...
git add .

echo.
echo [执行] 创建提交...
git commit -m "Initial commit: 智能客服工单自动处理系统"

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 下一步操作：
echo.
echo 1. 在GitHub创建新仓库（不要勾选Initialize with README）
echo 2. 复制仓库地址，然后运行：
echo.
echo    git remote add origin https://github.com/用户名/仓库名.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 或者使用GitHub Desktop直接推送
echo.
echo 提示：查看 UPLOAD_TO_GITHUB.md 获取详细指南
echo ========================================
pause
