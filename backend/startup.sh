#!/bin/bash
# =============================================
# 面智AI — Railway 部署启动脚本
# 1. 转换 Railway DATABASE_URL（mysql:// → mysql+asyncmy://, postgresql:// → postgresql+asyncpg://）
# 2. 运行数据库迁移
# 3. 启动 FastAPI 服务
# =============================================
set -e

echo "=== 面智AI 后端启动 ==="

# ── 1. 数据库连接字转换 ──────────────────────────
# Railway 提供的 DATABASE_URL 可能是 mysql:// 或 postgresql:// 格式
# 本项目需要异步驱动格式（mysql+asyncmy:// 或 postgresql+asyncpg://）
if [ -n "$DATABASE_URL" ]; then
    case "$DATABASE_URL" in
        mysql://*)
            export DATABASE_URL="mysql+asyncmy://${DATABASE_URL#mysql://}"
            echo "[OK] DATABASE_URL 已转换为 asyncmy 格式"
            ;;
        mysql+asyncmy://*)
            echo "[OK] DATABASE_URL 已是 asyncmy 格式"
            ;;
        postgresql://*)
            export DATABASE_URL="postgresql+asyncpg://${DATABASE_URL#postgresql://}"
            echo "[OK] DATABASE_URL 已转换为 asyncpg 格式"
            ;;
        postgresql+asyncpg://*)
            echo "[OK] DATABASE_URL 已是 asyncpg 格式"
            ;;
        *)
            echo "[OK] DATABASE_URL 使用原始格式"
            ;;
    esac
else
    echo "[!!] 未设置 DATABASE_URL，使用默认配置"
fi

# ── 2. 数据库迁移 ────────────────────────────────
echo "[..] 运行数据库迁移..."
cd /app/backend 2>/dev/null || cd "$(dirname "$0")"

if [ -d "alembic" ]; then
    alembic upgrade head
    echo "[OK] 数据库迁移完成"
else
    echo "[!!] 未找到 alembic 目录，跳过迁移"
fi

# ── 3. 启动服务 ──────────────────────────────────
PORT="${PORT:-8000}"
echo "[..] 启动 FastAPI 服务 (端口: $PORT)..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --proxy-headers \
    --forwarded-allow-ips '*'
