# 阶段 3A 进度记录

日期：2026-06-22

## 完成功能

- 新增 LangGraph 自适应追问 Agent。
- 新增 `PRIMARY` / `FOLLOW_UP` 题目类型。
- 新增当前题指针 `interview_sessions.current_question_id`。
- 新增会话追问计数 `interview_sessions.follow_up_count`。
- 新增 `interview_agent_events` 表记录 Agent 决策。
- 主问题评分后，Agent 可生成一道追问或进入下一道主问题。
- 追问作答后直接进入下一道主问题或报告阶段，不再触发二次追问。
- 0 分、明显“不会”、重复空洞回答不会强制追问。
- 报告数值分只聚合 `PRIMARY` 主问题评分。
- `FOLLOW_UP` 追问记录作为补充上下文传入报告 Prompt。
- 前端新增追问提示卡片和 Agent 决策时间线。
- 前端提交成功后优先使用后端返回的 `next_question`，避免继续使用上一题 ID。

## 新增 LangGraph 节点

```text
load_context
  -> check_follow_up_eligibility
  -> decide_follow_up
  -> create_follow_up | select_next_primary
  -> ready_for_report
```

节点说明：
- `load_context`：承载会话、题目、回答、评分和追问上限。
- `check_follow_up_eligibility`：检查题目类型、分数区间、单题追问上限和会话追问上限。
- `decide_follow_up`：调用 LLM 返回严格 JSON 决策。
- `create_follow_up`：进入服务层创建追问题目并设置当前题。
- `select_next_primary`：进入下一道主问题。
- `ready_for_report`：所有主问题和追问完成。

## 新增迁移文件

```text
backend/alembic/versions/b24e3a8f9c31_add_langgraph_follow_up_agent.py
```

新增或修改：
- `interview_questions.question_type`
- `interview_questions.parent_question_id`
- `interview_sessions.current_question_id`
- `interview_sessions.follow_up_count`
- `interview_agent_events`

## 修改文件

后端：
- `backend/app/agents/state.py`
- `backend/app/agents/interview_graph.py`
- `backend/app/core/config.py`
- `backend/app/models/interview_agent_event.py`
- `backend/app/models/interview_question.py`
- `backend/app/models/interview_session.py`
- `backend/app/prompts/follow_up_decision.py`
- `backend/app/schemas/agent.py`
- `backend/app/schemas/answer.py`
- `backend/app/schemas/interview.py`
- `backend/app/schemas/interview_question.py`
- `backend/app/schemas/llm.py`
- `backend/app/services/agent_service.py`
- `backend/app/services/evaluation_service.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/question_service.py`
- `backend/app/services/report_service.py`
- `backend/app/api/v1/interviews.py`
- `backend/alembic/env.py`
- `backend/app/models/__init__.py`

前端：
- `frontend/src/api/types.ts`
- `frontend/src/api/interviews.ts`
- `frontend/src/components/AgentFollowUpNotice.tsx`
- `frontend/src/components/AgentEventTimeline.tsx`
- `frontend/src/components/InterviewProgress.tsx`
- `frontend/src/components/InterviewReport.tsx`
- `frontend/src/pages/InterviewDetailPage.tsx`

文档：
- `README.md`
- `docs/architecture.md`
- `docs/api-design.md`
- `docs/database-design.md`
- `docs/prompt-design.md`
- `docs/progress/phase-3a.md`

## 新增测试

`backend/tests/test_phase3a_followups.py` 覆盖：
- 主问题回答可创建追问，`GET /current-question` 返回追问题。
- 追问作答后进入下一道主问题，且不会形成追问循环。
- 会话追问上限命中后回退到主问题流程。
- 0 分“不会”类回答不触发追问。
- 报告数值分只使用主问题评分，追问记录仍进入报告 Prompt。
- 用户不能读取其他用户会话的 Agent 事件。

## 测试命令与结果

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

当前结果：
- `pytest`：45 passed
- `ruff check .`：All checks passed

前端：

```powershell
cd frontend
npm run build
```

当前结果：
- `npm run build`：通过
- Vite 提示 chunk 超过 500 kB，主要来自图表依赖，不影响功能。

## 手工验证路径

1. 执行数据库迁移到最新版本。
2. 启动后端和前端。
3. 登录后创建新会话并开始文本面试。
4. 对主问题输入有部分技术内容但不完整的回答。
5. 如果 Agent 返回追问，页面应显示“AI 生成了一道追问”。
6. 点击“回答 AI 追问”，输入追问回答并提交。
7. 页面应进入下一道主问题，不得继续对追问生成追问。
8. 完成全部主问题和追问后进入 `READY_FOR_REPORT`。
9. 生成报告后，综合分应只反映主问题评分，追问作为诊断上下文。
10. 刷新页面后，当前题应从后端 `current_question_id` 恢复。

## 已知限制

- 当前前端没有独立前端测试框架，本阶段未引入大型测试框架。
- 追问决策依赖 LLM JSON 输出，后端会校验结构并在失败时回退到下一道主问题。
- 当前不实现语音输入、RAG、虚拟人和历史趋势分析。

## 下一阶段建议

阶段 3B 可以实现语音输入或 RAG，但仍应保持自动化测试不调用真实外部 API。

## 建议 Git commit message

```text
feat: add langgraph adaptive follow-up agent
```
