# Phase 0：工程骨架与环境验证

## 完成功能

- 初始化 Git 仓库并设置主分支为 `main`，未提交。
- 初始化 React + TypeScript + Vite 前端项目。
- 安装前端依赖：React Router、Axios、Zustand、TanStack Query、Ant Design、Ant Design Icons、ECharts、echarts-for-react。
- 初始化 FastAPI 后端项目和 Python 虚拟环境。
- 安装后端依赖并生成 `backend/requirements.txt`。
- 实现 `/health` 健康检查接口。
- 配置 CORS，允许 `http://localhost:5173` 和 `http://127.0.0.1:5173`。
- 建立 SQLAlchemy Async、Pydantic Settings、Alembic 基础结构。
- 创建最小 Pytest 测试。
- 创建 README、环境文档、架构文档和开发约束文档。

## 修改文件

- `.env.example`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `docs/architecture.md`
- `docs/environment-setup.md`
- `docs/progress/phase-0.md`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/index.css`
- `backend/requirements.txt`
- `backend/pyproject.toml`
- `backend/app/main.py`
- `backend/app/api/router.py`
- `backend/app/api/health.py`
- `backend/app/core/config.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/logging.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/README.md`
- `backend/tests/test_health.py`

## 启动命令

前端：

```powershell
cd frontend
npm run dev
```

后端：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

## 测试命令

```powershell
cd frontend
npm run build
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

## 测试结果

- `npm run build`：通过。Vite 构建成功，提示单个 chunk 超过 500 kB。
- `ruff check .`：通过，输出 `All checks passed!`。
- `pytest`：通过，`1 passed, 1 warning`。警告来自 FastAPI/Starlette TestClient 的 httpx 兼容提示。
- `/health`：通过，`StatusCode: 200`，返回 `{"status":"ok","service":"ai-interview-api","timestamp":"2026-06-21T17:58:37.754381+00:00"}`。

## 已知限制

- 当前阶段不实现登录、JWT、数据库表、面试业务、语音、RAG 或虚拟人。
- 当前阶段不读取真实 API Key。
- 当前阶段不在服务启动时连接真实数据库。
- Windows PowerShell 的 `Invoke-WebRequest` 在当前环境需要加 `-UseBasicParsing`，否则会触发 IE 引擎不可用提示。

## 下一步建议

进入阶段 1 前，确认认证方案、用户角色、数据库迁移规范和基础 UI 布局。

## 建议 Git commit message

```text
chore: initialize phase 0 project scaffold
```
