# Phase 1：用户认证与面试会话基础功能

## 完成功能

- 后端支持注册、登录、JWT 签发、获取当前用户。
- 后端支持创建空面试会话、查询当前用户会话列表、查询当前用户会话详情。
- 后端新增 `users` 与 `interview_sessions` SQLAlchemy 模型。
- 后端新增 Alembic 首个迁移文件。
- 前端新增注册、登录、Dashboard、创建面试、会话详情页面。
- 前端使用 React Router、Ant Design、TanStack Query、Axios、Zustand。
- 前端 Dashboard 真实请求 `/health` 展示后端联通状态。
- 后端测试覆盖注册、重复注册、登录、错误密码、鉴权、会话创建、用户隔离和跨用户 404。

## 修改文件

- `.env.example`
- `README.md`
- `docs/api-design.md`
- `docs/database-design.md`
- `docs/progress/phase-1.md`
- `backend/requirements.txt`
- `backend/alembic/env.py`
- `backend/alembic/versions/6fba3a7c8156_create_users_and_interview_sessions.py`
- `backend/app/api/deps.py`
- `backend/app/api/router.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/interviews.py`
- `backend/app/api/v1/router.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/db/base.py`
- `backend/app/models/user.py`
- `backend/app/models/interview_session.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/common.py`
- `backend/app/schemas/interview.py`
- `backend/app/schemas/user.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/interview_service.py`
- `backend/tests/test_phase1_auth_interviews.py`
- `frontend/.env.example`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/api/client.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/api/health.ts`
- `frontend/src/api/interviews.ts`
- `frontend/src/api/types.ts`
- `frontend/src/pages/AppLayout.tsx`
- `frontend/src/pages/AuthShell.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/InterviewDetailPage.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/NewInterviewPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/stores/auth.ts`

## 数据库迁移命令与结果

已生成迁移文件：

```text
backend/alembic/versions/6fba3a7c8156_create_users_and_interview_sessions.py
```

尝试执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

结果：已执行成功。Alembic 输出：

```text
Running upgrade  -> 6fba3a7c8156, create_users_and_interview_sessions
```

MySQL 表验证结果：

```text
alembic_version
interview_sessions
users
```

## 前后端启动命令

后端：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

前端：

```powershell
cd frontend
npm run dev
```

## 测试命令

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

```powershell
cd frontend
npm run build
```

## 测试结果

- `pytest`：通过，`10 passed, 2 warnings`。
- `ruff check .`：通过，`All checks passed!`。
- `npm run build`：通过。Vite 构建成功，有单个 chunk 超过 500 kB 的提示。

## 已知限制

- 当前阶段不实现 LLM、LangGraph 工作流、文本问答、语音、RAG 或虚拟人。
- 当前阶段只创建空面试会话，不创建题目、回答、评分或报告表。
- 测试中 SQLite DLL 需要提升权限运行；普通沙箱内会出现 `_sqlite3` DLL 加载被拒绝。
- `passlib 1.7.4` 与 `bcrypt 5.0.0` 不兼容，已固定 `bcrypt==4.0.1`。

## 下一阶段建议

阶段 2 可以接入题目结构、面试问题流转和基础文本回答记录，但仍建议先保持非 LLM 的可测试业务闭环。

## 建议 Git commit message

```text
feat: add phase 1 auth and interview session foundation
```
