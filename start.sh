#!/bin/bash
#
# 面智AI — 前后端一键启动脚本
# 用法: bash start.sh [--skip-db-check] [--install]
#

set -e

# =============================================
# 颜色定义
# =============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# =============================================
# 参数解析
# =============================================
SKIP_DB_CHECK=false
FORCE_INSTALL=false

for arg in "$@"; do
    case $arg in
        --skip-db-check) SKIP_DB_CHECK=true ;;
        --install)       FORCE_INSTALL=true ;;
        -h|--help)
            echo "用法: bash start.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --skip-db-check   跳过 MySQL 连接检查"
            echo "  --install         强制重新安装依赖"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
    esac
done

# =============================================
# 项目路径
# =============================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

PIDS=()

# =============================================
# 工具函数
# =============================================
print_banner() {
    echo ""
    echo -e "${BLUE}${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}${BOLD}║       🎯  面智AI  智能面试平台      ║${NC}"
    echo -e "${BLUE}${BOLD}╚══════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}[..]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[!!]${NC} $1"
}

print_err() {
    echo -e "${RED}[XX]${NC} $1"
}

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服务...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo -e "  ${GREEN}✓${NC} 已停止 PID: $pid"
        fi
    done
    echo -e "${GREEN}所有服务已停止。再见！${NC}"
    exit 0
}

trap cleanup INT TERM

# =============================================
# 环境检查
# =============================================
check_prerequisites() {
    echo -e "${BOLD}━━━━━━━━━━ 环境检查 ━━━━━━━━━━${NC}"

    # Python
    if command -v python &>/dev/null; then
        PY_VER=$(python --version 2>&1)
        print_ok "Python: $PY_VER"
    elif command -v python3 &>/dev/null; then
        PY_VER=$(python3 --version 2>&1)
        print_ok "Python: $PY_VER"
    else
        print_err "未找到 Python，请安装 Python 3.12+"
        exit 1
    fi

    # Node.js
    if command -v node &>/dev/null; then
        NODE_VER=$(node --version)
        print_ok "Node.js: $NODE_VER"
    else
        print_err "未找到 Node.js，请安装 Node.js 24+"
        exit 1
    fi

    # npm
    if command -v npm &>/dev/null; then
        NPM_VER=$(npm --version)
        print_ok "npm: v$NPM_VER"
    else
        print_err "未找到 npm"
        exit 1
    fi

    # MySQL (可选检查)
    if [ "$SKIP_DB_CHECK" = false ]; then
        if command -v mysql &>/dev/null; then
            MYSQL_VER=$(mysql --version 2>&1)
            print_ok "MySQL: $MYSQL_VER"
        else
            print_warn "未找到 mysql 客户端，跳过数据库检查"
            print_warn "请确保 MySQL 服务正在运行"
        fi
    else
        print_warn "已跳过 MySQL 检查"
    fi

    # .env 文件
    if [ -f "$SCRIPT_DIR/.env" ]; then
        print_ok "已找到 .env 配置文件"
    else
        print_warn "未找到 .env，将使用默认配置（部分功能可能不可用）"
    fi

    echo ""
}

# =============================================
# 依赖安装
# =============================================
install_dependencies() {
    echo -e "${BOLD}━━━━━━━━━━ 依赖检查 ━━━━━━━━━━${NC}"

    # --- 后端 ---
    if [ ! -d "$BACKEND_DIR/.venv" ] || [ "$FORCE_INSTALL" = true ]; then
        print_step "创建后端虚拟环境..."
        python -m venv "$BACKEND_DIR/.venv"
        print_ok "虚拟环境已创建"
    fi

    print_step "激活虚拟环境 & 安装后端依赖..."
    source "$BACKEND_DIR/.venv/Scripts/activate" 2>/dev/null || \
    source "$BACKEND_DIR/.venv/bin/activate" 2>/dev/null

    if [ "$FORCE_INSTALL" = true ] || ! python -c "import fastapi" 2>/dev/null; then
        pip install -r "$BACKEND_DIR/requirements.txt" -q
        print_ok "后端依赖已安装"
    else
        print_ok "后端依赖已就绪"
    fi

    # --- 前端 ---
    if [ "$FORCE_INSTALL" = true ] || [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        print_step "安装前端依赖..."
        cd "$FRONTEND_DIR" && npm install --silent
        print_ok "前端依赖已安装"
    else
        print_ok "前端依赖已就绪"
    fi

    echo ""
}

# =============================================
# 启动服务
# =============================================
start_services() {
    echo -e "${BOLD}━━━━━━━━━━ 启动服务 ━━━━━━━━━━${NC}"

    # --- 后端 ---
    print_step "启动后端 (FastAPI) ..."
    source "$BACKEND_DIR/.venv/Scripts/activate" 2>/dev/null || \
    source "$BACKEND_DIR/.venv/bin/activate" 2>/dev/null

    cd "$BACKEND_DIR"
    uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    PIDS+=("$BACKEND_PID")
    print_ok "后端已启动  |  PID: $BACKEND_PID  |  http://127.0.0.1:8000"

    # 等后端就绪
    print_step "等待后端就绪..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            print_ok "后端健康检查通过"
            break
        fi
        if [ "$i" -eq 30 ]; then
            print_warn "后端启动超时，请检查 http://127.0.0.1:8000/health"
        fi
        sleep 1
    done

    # --- 前端 ---
    print_step "启动前端 (Vite) ..."
    cd "$FRONTEND_DIR"
    npm run dev &
    FRONTEND_PID=$!
    PIDS+=("$FRONTEND_PID")
    print_ok "前端已启动  |  PID: $FRONTEND_PID  |  http://localhost:5173"

    echo ""
}

# =============================================
# 启动完成
# =============================================
show_summary() {
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}${BOLD}✓ 面智AI 启动成功！${NC}"
    echo ""
    echo -e "  ${CYAN}前端页面:${NC}  ${BOLD}http://localhost:5173${NC}"
    echo -e "  ${CYAN}后端接口:${NC}  ${BOLD}http://127.0.0.1:8000${NC}"
    echo -e "  ${CYAN}API 文档:${NC}  ${BOLD}http://127.0.0.1:8000/docs${NC}"
    echo ""
    echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${NC}"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# =============================================
# 主流程
# =============================================
print_banner
check_prerequisites
install_dependencies
start_services
show_summary

# 等待任意子进程退出（保持脚本运行）
wait
