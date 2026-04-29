#!/bin/bash

echo "========================================"
echo "智能客服系统 - 启动服务"
echo "========================================"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "[警告] 未找到.env文件"
    echo "请复制 .env.example 为 .env 并配置API密钥"
    echo ""
    exit 1
fi

echo "[√] 环境配置检查通过"
echo ""
echo "正在启动服务..."
echo "访问 http://localhost:8000/docs 查看API文档"
echo "按 Ctrl+C 停止服务"
echo ""

python src/new_agent.py
