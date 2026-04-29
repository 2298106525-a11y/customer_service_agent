# 智能客服系统 - GitHub打包助手 (PowerShell版本)
# 此脚本使用UTF-8编码，完美支持中文显示

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "智能客服系统 - GitHub打包助手" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查src目录和文件
Write-Host "[检查] 验证项目文件..." -ForegroundColor Yellow
if (Test-Path "src\new_agent.py") {
    Write-Host "[OK] src\new_agent.py 已存在" -ForegroundColor Green
} else {
    Write-Host "[错误] 缺少 src\new_agent.py" -ForegroundColor Red
    Write-Host ""
    Write-Host "请确认您已完成以下步骤：" -ForegroundColor Yellow
    Write-Host "1. 主程序文件应该在 src\new_agent.py" -ForegroundColor Yellow
    Write-Host "2. 如果文件在根目录，请运行: move new_agent.py src\" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

if (-not (Test-Path "README.md")) {
    Write-Host "[警告] 缺少 README.md" -ForegroundColor Yellow
}

if (-not (Test-Path "requirements.txt")) {
    Write-Host "[警告] 缺少 requirements.txt" -ForegroundColor Yellow
}

if (-not (Test-Path ".gitignore")) {
    Write-Host "[警告] 缺少 .gitignore" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[检查] Git状态..." -ForegroundColor Yellow

if (Test-Path ".git") {
    Write-Host "[OK] Git仓库已初始化" -ForegroundColor Green
    Write-Host ""
    git status
    Write-Host ""
    $confirm = Read-Host "是否继续提交？(Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "操作已取消" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 0
    }
} else {
    Write-Host "[信息] 未检测到Git仓库，正在初始化..." -ForegroundColor Yellow
    
    # 检查Git是否安装
    try {
        $null = Get-Command git -ErrorAction Stop
    } catch {
        Write-Host "[错误] Git未安装！" -ForegroundColor Red
        Write-Host ""
        Write-Host "请先安装Git: https://git-scm.com/download/win" -ForegroundColor Yellow
        Write-Host "或使用GitHub Desktop" -ForegroundColor Yellow
        Read-Host "按回车键退出"
        exit 1
    }
    
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] Git初始化失败" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
    Write-Host "[OK] Git仓库创建成功" -ForegroundColor Green
}

Write-Host ""
Write-Host "[执行] 添加文件到Git..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "[执行] 创建提交..." -ForegroundColor Yellow
git commit -m "Initial commit: 智能客服工单自动处理系统"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "打包完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 在GitHub创建新仓库（不要勾选Initialize with README）" -ForegroundColor White
Write-Host "2. 复制仓库地址，然后运行：" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/用户名/仓库名.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "或者使用GitHub Desktop直接推送" -ForegroundColor White
Write-Host ""
Write-Host "提示：查看 UPLOAD_TO_GITHUB.md 获取详细指南" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Green

Read-Host "按回车键退出"
