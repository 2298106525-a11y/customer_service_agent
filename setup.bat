@echo off
echo ========================================
echo 智能客服系统 - 环境设置脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/4] Python版本检查通过
python --version
echo.

REM 创建虚拟环境
echo [2/4] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)
echo.

REM 激活虚拟环境
echo [3/4] 激活虚拟环境...
call venv\Scripts\activate.bat
echo 虚拟环境已激活
echo.

REM 安装依赖
echo [4/4] 安装依赖包...
pip install -r requirements.txt
echo.

echo ========================================
echo 环境设置完成！
echo ========================================
echo.
echo 下一步：
echo 1. 复制 .env.example 为 .env
echo 2. 编辑 .env 文件，填入API密钥
echo 3. 运行 start.bat 启动服务
echo.
pause
