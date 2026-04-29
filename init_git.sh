#!/bin/bash
# Git初始化脚本

echo "========================================"
echo "初始化Git仓库"
echo "========================================"
echo ""

# 检查是否已初始化
if [ -d ".git" ]; then
    echo "[提示] Git仓库已存在"
    echo ""
    read -p "是否重新初始化？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    rm -rf .git
fi

# 初始化Git
git init
echo "[√] Git仓库初始化完成"
echo ""

# 添加所有文件
git add .
echo "[√] 文件已添加到暂存区"
echo ""

# 首次提交
git commit -m "Initial commit: 智能客服工单自动处理系统"
echo "[√] 首次提交完成"
echo ""

echo "========================================"
echo "下一步操作："
echo "========================================"
echo ""
echo "1. 在GitHub上创建新仓库"
echo "2. 运行以下命令关联远程仓库："
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "========================================"
