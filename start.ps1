# =============================================
# 面智AI — 前后端一键启动脚本 (PowerShell)
# 用法: .\start.ps1 [-SkipDbCheck] [-Install]
# =============================================

param(
    [switch]$SkipDbCheck,
    [switch]$Install
)

$ErrorActionPreference = "Stop"

# =============================================
# 项目路径
# =============================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"

$BackendPid = $null
$FrontendPid = $null

# =============================================
# 工具函数
# =============================================
function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║       🎯  面智AI  智能面试平台      ║" -ForegroundColor Blue
    Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

function Write-Step {
    Write-Host "[..] $args" -ForegroundColor Cyan
}

function Write-Ok {
    Write-Host "[OK] $args" -ForegroundColor Green
}

function Write-Warn {
    Write-Host "[!!] $args" -ForegroundColor Yellow
}

function Write-Err {
    Write-Host "[XX] $args" -ForegroundColor Red
}

# =============================================
# Ctrl+C 清理
# =============================================
function Cleanup {
    Write-Host ""
    Write-Host "正在停止所有服务..." -ForegroundColor Yellow

    if ($FrontendPid) {
        Stop-Process -Id $FrontendPid -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已停止前端 (PID: $FrontendPid)" -ForegroundColor Green
    }
    if ($BackendPid) {
        Stop-Process -Id $BackendPid -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已停止后端 (PID: $BackendPid)" -ForegroundColor Green
    }

    Write-Host "所有服务已停止。再见！" -ForegroundColor Green
    exit 0
}

# 注册 Ctrl+C 处理
try {
    [Console]::TreatControlCAsInput = $false
} catch {}
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

# =============================================
# 环境检查
# =============================================
function Check-Prerequisites {
    Write-Host "━━━━━━━━━━ 环境检查 ━━━━━━━━━━" -ForegroundColor White

    # Python
    try {
        $pyVer = python --version 2>&1
        Write-Ok "Python: $pyVer"
    } catch {
        try {
            $pyVer = python3 --version 2>&1
            Write-Ok "Python: $pyVer"
        } catch {
            Write-Err "未找到 Python，请安装 Python 3.12+"
            exit 1
        }
    }

    # Node.js
    try {
        $nodeVer = node --version 2>&1
        Write-Ok "Node.js: $nodeVer"
    } catch {
        Write-Err "未找到 Node.js，请安装 Node.js 24+"
        exit 1
    }

    # npm
    try {
        $npmVer = npm --version 2>&1
        Write-Ok "npm: v$npmVer"
    } catch {
        Write-Err "未找到 npm"
        exit 1
    }

    # MySQL
    if (-not $SkipDbCheck) {
        try {
            $mysqlVer = mysql --version 2>&1
            Write-Ok "MySQL: $mysqlVer"
        } catch {
            Write-Warn "未找到 mysql 客户端，跳过数据库检查"
            Write-Warn "请确保 MySQL 服务正在运行"
        }
    } else {
        Write-Warn "已跳过 MySQL 检查"
    }

    # .env
    $envFile = Join-Path $ScriptDir ".env"
    if (Test-Path $envFile) {
        Write-Ok "已找到 .env 配置文件"
    } else {
        Write-Warn "未找到 .env，将使用默认配置（部分功能可能不可用）"
    }

    Write-Host ""
}

# =============================================
# 依赖安装
# =============================================
function Install-Dependencies {
    Write-Host "━━━━━━━━━━ 依赖检查 ━━━━━━━━━━" -ForegroundColor White

    # --- 后端 ---
    $venvPath = Join-Path $BackendDir ".venv"
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

    if (-not (Test-Path $venvPath) -or $Install) {
        Write-Step "创建后端虚拟环境..."
        python -m venv $venvPath
        Write-Ok "虚拟环境已创建"
    }

    Write-Step "激活虚拟环境 & 安装后端依赖..."
    & $activateScript

    $fastapiInstalled = python -c "import fastapi" 2>&1
    if ($Install -or $LASTEXITCODE -ne 0) {
        pip install -r (Join-Path $BackendDir "requirements.txt") -q
        Write-Ok "后端依赖已安装"
    } else {
        Write-Ok "后端依赖已就绪"
    }

    # --- 前端 ---
    $nodeModules = Join-Path $FrontendDir "node_modules"
    if ($Install -or -not (Test-Path $nodeModules)) {
        Write-Step "安装前端依赖..."
        Push-Location $FrontendDir
        npm install --silent
        Pop-Location
        Write-Ok "前端依赖已安装"
    } else {
        Write-Ok "前端依赖已就绪"
    }

    Write-Host ""
}

# =============================================
# 启动服务
# =============================================
function Start-Services {
    Write-Host "━━━━━━━━━━ 启动服务 ━━━━━━━━━━" -ForegroundColor White

    # --- 后端 ---
    Write-Step "启动后端 (FastAPI) ..."
    $activateScript = Join-Path $BackendDir ".venv\Scripts\Activate.ps1"
    & $activateScript

    $backendProc = Start-Process -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$BackendDir'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
    ) -PassThru
    $script:BackendPid = $backendProc.Id
    Write-Ok "后端已启动  |  PID: $BackendPid  |  http://127.0.0.1:8000"

    # 等后端就绪
    Write-Step "等待后端就绪..."
    $ready = $false
    for ($i = 1; $i -le 15; $i++) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Ok "后端健康检查通过"
                $ready = $true
                break
            }
        } catch {}
    }
    if (-not $ready) {
        Write-Warn "后端启动超时，请检查 http://127.0.0.1:8000/health"
    }

    # --- 前端 ---
    Write-Step "启动前端 (Vite) ..."
    $frontendProc = Start-Process -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$FrontendDir'; npm run dev"
    ) -PassThru
    $script:FrontendPid = $frontendProc.Id
    Write-Ok "前端已启动  |  PID: $FrontendPid  |  http://localhost:5173"

    Write-Host ""
}

# =============================================
# 启动完成
# =============================================
function Show-Summary {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
    Write-Host ""
    Write-Host "  ✓ 面智AI 启动成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "  前端页面:  " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:5173" -ForegroundColor White
    Write-Host "  后端接口:  " -NoNewline -ForegroundColor Cyan
    Write-Host "http://127.0.0.1:8000" -ForegroundColor White
    Write-Host "  API 文档:  " -NoNewline -ForegroundColor Cyan
    Write-Host "http://127.0.0.1:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "  按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
    Write-Host ""
}

# =============================================
# 主流程
# =============================================
Write-Banner
Check-Prerequisites
Install-Dependencies
Start-Services
Show-Summary

Write-Host "服务运行中，关闭此窗口即可停止..." -ForegroundColor DarkGray
Write-Host ""

# 保持脚本运行
while ($true) {
    Start-Sleep -Seconds 5
}
