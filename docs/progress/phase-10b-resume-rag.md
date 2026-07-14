# Phase 10B：用户简历管理与简历增强面试（Resume-RAG）

## 完成功能

- 新增“我的简历”模块，支持上传 PDF/TXT/MD 或粘贴简历文本。
- PDF 简历解析依赖统一声明为 `pypdf`，缺失依赖时继续返回明确容错提示。
- 支持多份简历版本管理、启用、停用、软删除和查看脱敏解析内容。
- 新增 `use_active_resume` 创建面试开关；没有启用简历或本场关闭时，面试流程保持原逻辑。
- 开始面试生成题目前，按 `target_role + difficulty + interview_type` 检索当前启用简历 Top-K 片段，并写入会话简历快照。
- 题目生成 Prompt 新增 Resume-RAG 上下文和 Prompt 注入防护说明。
- LangGraph 追问决策可读取当场脱敏简历快照作为事实背景，不改变追问状态机。
- 面试详情元信息显示“本场已引用简历：xxx”，不展示完整简历内容。
- 简历文本进入 Embedding 和 Prompt 前执行邮箱、手机号和明显地址字段脱敏。

## 修改文件

- `README.md`
- `docs/architecture.md`
- `docs/progress/phase-10b-resume-rag.md`
- `backend/alembic/env.py`
- `backend/alembic/versions/d4f0b7a2c91e_add_resume_rag.py`
- `backend/pyproject.toml`
- `backend/requirements.txt`
- `backend/app/agents/state.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/resumes.py`
- `backend/app/models/__init__.py`
- `backend/app/models/interview_resume_link.py`
- `backend/app/models/interview_session.py`
- `backend/app/models/resume_chunk.py`
- `backend/app/models/user_resume.py`
- `backend/app/prompts/follow_up_decision.py`
- `backend/app/prompts/question_generation.py`
- `backend/app/schemas/interview.py`
- `backend/app/schemas/resume.py`
- `backend/app/services/agent_service.py`
- `backend/app/services/interview_service.py`
- `backend/app/services/knowledge_base_service.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/question_service.py`
- `backend/app/services/resume_service.py`
- `backend/app/services/vector_utils.py`
- `backend/tests/test_phase10b_resume_rag.py`
- `frontend/src/App.tsx`
- `frontend/src/api/resumes.ts`
- `frontend/src/api/types.ts`
- `frontend/src/index.css`
- `frontend/src/pages/AppLayout.tsx`
- `frontend/src/pages/InterviewDetailPage.tsx`
- `frontend/src/pages/NewInterviewPage.tsx`
- `frontend/src/pages/ResumePage.tsx`
- `frontend/src/types/resume.ts`

## 新增数据库对象

- Alembic revision：`d4f0b7a2c91e_add_resume_rag`
- `user_resumes`：保存当前用户的简历版本、脱敏解析文本、状态、启用标记和软删除时间。
- `resume_chunks`：保存简历分块、JSON 向量和 Embedding 元数据。
- `interview_resume_links`：保存当场面试引用的简历 id、标题快照和脱敏检索片段快照。
- `interview_sessions.use_active_resume`：保存本场是否启用简历增强。

## 新增接口

- `GET /api/v1/resumes`
- `GET /api/v1/resumes/{resume_id}`
- `POST /api/v1/resumes/upload`
- `POST /api/v1/resumes/paste`
- `PATCH /api/v1/resumes/{resume_id}`
- `POST /api/v1/resumes/{resume_id}/activate`
- `POST /api/v1/resumes/{resume_id}/deactivate`
- `DELETE /api/v1/resumes/{resume_id}`

## Resume-RAG 数据流

```text
上传或粘贴简历
  -> 解析与规范化
  -> 隐私脱敏
  -> 复用 split_text_into_chunks 分块
  -> 复用 EmbeddingClient 生成 MySQL JSON 向量
  -> 保存 resume_chunks

开始面试
  -> 检查 interview_sessions.use_active_resume
  -> 查询当前用户 READY 且启用的简历
  -> 复用余弦相似度检索 Top-K 简历片段
  -> 写入 interview_resume_links 快照
  -> 注入题目生成 Prompt
```

## 兼容关系

- 未启用简历或本场关闭简历增强时，不创建简历快照，不向模型发送简历内容。
- PDF 简历解析使用正式后端依赖 `pypdf`，不额外引入其他 PDF 解析库；依赖缺失时仍返回“PDF 解析依赖未安装，请安装 pypdf。”。
- 原知识库 RAG 保持独立，Resume-RAG 只作为额外上下文。
- LangGraph 状态机、评分、报告生成、ASR、浏览器 TTS、讯飞数字人生命周期均未改变。
- 旧会话没有简历快照时，接口返回 `resume: null`，前端显示“未引用”。
- 删除简历为软删除，不影响旧会话的标题和上下文快照。

## 启动命令

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
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .

cd frontend
npm run build
```

## 测试结果

- `python -m pip install -e .`：通过，确认 `pyproject.toml` 中的 `pypdf` 会随本地可编辑安装进入后端运行环境。
- `python -m pytest tests/test_phase10b_resume_rag.py`：通过，`11 passed, 2 warnings`，覆盖 TXT / MD / PDF 简历上传解析链路。
- `python -m pytest`：通过，`83 passed, 2 warnings`。
- `python -m ruff check .`：通过，`All checks passed!`。
- `python -m compileall app tests`：通过。
- `python -m alembic heads`：通过，当前 head 为 `d4f0b7a2c91e`。
- `npm run build`：通过；Vite 仍提示部分 chunk 超过 500 kB。

## 手工测试清单

1. 登录后进入“我的简历”。
2. 粘贴简历文本并确认状态为 READY。
3. 上传 TXT / MD / PDF 简历并确认可启用。
4. 切换启用简历，确认同一用户最多一份当前启用简历。
5. 查看解析内容，确认邮箱、手机号、明显地址字段已脱敏。
6. 删除已启用简历，确认仅软删除且旧会话仍能显示引用标题。
7. 创建面试页存在“结合我的简历提问”开关。
8. 无启用简历时创建面试仍可正常开始。
9. 启用简历后创建并开始面试，确认详情页显示“引用简历”。
10. 本场关闭简历增强时，面试不显示引用简历。
11. 知识库 RAG、LangGraph 追问、评分、报告、ASR、虚拟人流程不回归。

## 已知限制

- 未引入 OCR 或 DOC/DOCX 解析。
- 简历上传后同步解析和向量化，超大简历会受现有 RAG 文件大小限制。
- 同一用户仅通过服务事务保证最多一份启用简历，当前迁移未使用数据库部分唯一索引。

## 下一步建议

- 在可连接本地数据库的环境执行 `alembic upgrade head`、`alembic current` 和完整 pytest。
- 为“我的简历”页面增加 Playwright 冒烟测试。
- 后续可增加简历内容分段预览和简历与岗位匹配度提示，但不要暴露联系方式。

## 建议 Git commit message

```text
feat(resume): add resume rag interview enhancement
```
