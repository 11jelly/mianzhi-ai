# Phase 2A：文本面试题生成与展示

## 完成功能

- 新增 `interview_questions` 模型和表结构。
- 新增百炼 Qwen OpenAI-compatible LLM Client 封装。
- 新增题目生成 Prompt 和 LLM 输出 Pydantic 校验。
- 新增开始文本面试接口。
- 新增当前题目和题目列表接口。
- 开始面试成功后，题目持久化到 MySQL，会话状态更新为 `IN_PROGRESS`。
- 重复调用开始接口不会重复调用 LLM 或重复生成题目。
- 前端会话详情页支持开始文本面试和当前题展示。
- 自动化测试使用 Fake LLM，不调用真实百炼 API。

## 修改文件

- `.env.example`
- `README.md`
- `docs/api-design.md`
- `docs/database-design.md`
- `docs/prompt-design.md`
- `docs/progress/phase-2a.md`
- `backend/alembic/env.py`
- `backend/alembic/versions/841c566025ec_add_interview_questions.py`
- `backend/app/core/config.py`
- `backend/app/models/interview_question.py`
- `backend/app/models/interview_session.py`
- `backend/app/models/__init__.py`
- `backend/app/prompts/question_generation.py`
- `backend/app/schemas/interview.py`
- `backend/app/schemas/interview_question.py`
- `backend/app/schemas/llm.py`
- `backend/app/services/interview_service.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/question_service.py`
- `backend/app/api/v1/interviews.py`
- `backend/tests/test_phase2a_questions.py`
- `frontend/src/api/interviews.ts`
- `frontend/src/api/types.ts`
- `frontend/src/pages/InterviewDetailPage.tsx`
- `frontend/src/index.css`

## 数据库迁移名称、命令和结果

迁移文件：

```text
backend/alembic/versions/841c566025ec_add_interview_questions.py
```

执行命令：

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

结果：

```text
Running upgrade 6fba3a7c8156 -> 841c566025ec, add_interview_questions
```

MySQL 表验证：

```text
alembic_version
interview_questions
interview_sessions
users
```

## 后端接口列表

- `POST /api/v1/interviews/{session_id}/start`
- `GET /api/v1/interviews/{session_id}/current-question`
- `GET /api/v1/interviews/{session_id}/questions`

阶段 1 接口保持兼容。

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

- `pytest`：通过，`16 passed, 2 warnings`。
- `ruff check .`：通过，`All checks passed!`。
- `npm run build`：通过。Vite 构建成功，有单个 chunk 超过 500 kB 的提示。

## 已知限制

- 当前阶段不实现回答提交、AI 评分、报告、LangGraph、追问、语音、RAG 或虚拟人。
- 当前阶段 `current_question_index` 固定为 `0`，只展示第 1 题。
- 前端不展示 `expected_points`。
- 自动化测试不调用真实百炼 API。

## 下一步建议

阶段 2B 可以实现回答提交、单题保存和基础评分接口，继续保持可测试的服务层边界。

## 建议 Git commit message

```text
feat: add phase 2a question generation flow
```
