#!/bin/bash

echo "========================================"
echo "智能客服系统 - 环境设置脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.9+"
    exit 1
fi

echo "[1/4] Python版本检查通过"
python3 --version
echo ""

# 创建虚拟环境
echo "[2/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi
echo ""

# 激活虚拟环境
echo "[3/4] 激活虚拟环境..."
source venv/bin/activate
echo "虚拟环境已激活"
echo ""

# 安装依赖
echo "[4/4] 安装依赖包..."
pip install -r requirements.txt
echo ""

echo "========================================"
echo "环境设置完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 复制 .env.example 为 .env"
echo "2. 编辑 .env 文件，填入API密钥"
echo "3. 运行 ./start.sh 启动服务"
echo ""
