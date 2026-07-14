# 数据库设计

当前阶段包含七张业务表：`users`、`interview_sessions`、`interview_questions`、`interview_answers`、`answer_evaluations`、`interview_reports`、`interview_agent_events`。

## interview_sessions

保存用户创建的面试会话基础信息。

关键字段：
- `id`：UUID 字符串主键。
- `user_id`：关联 `users.id`。
- `target_role`：目标岗位。
- `difficulty`：`junior`、`intermediate`、`senior`。
- `interview_type`：`technical`、`project`、`comprehensive`。
- `question_count`：`3`、`5`、`8`。
- `current_question_index`：已完成主问题数量。
- `current_question_id`：当前可作答题目，可能指向主问题或追问。
- `follow_up_count`：当前会话已生成追问数量。
- `status`：`CREATED`、`IN_PROGRESS`、`READY_FOR_REPORT`、`COMPLETED`。

## interview_questions

保存主问题和 Agent 追问。

关键字段：
- `id`：UUID 字符串主键。
- `session_id`：关联 `interview_sessions.id`。
- `sequence`：题目序号，主问题按 1 到 `question_count` 生成，追问使用追加序号。
- `category`：题目分类。
- `question_text`：题干。
- `expected_points`：主问题参考要点，追问可为空。
- `question_type`：`PRIMARY` 或 `FOLLOW_UP`。
- `parent_question_id`：追问所属主问题，主问题为空。

约束：
- 同一会话内 `sequence` 唯一。
- `parent_question_id` 自引用 `interview_questions.id`。

## interview_reports

保存综合诊断报告。

字段：
- `id`：UUID 字符串主键。
- `session_id`：关联 `interview_sessions.id`，唯一。
- `overall_score`：综合分，0 到 100。
- `logic_score`：逻辑结构，0 到 25。
- `technical_score`：技术准确性，0 到 30。
- `expression_score`：表达清晰度，0 到 20。
- `project_depth_score`：项目深度，0 到 25。
- `summary`：综合评价。
- `strengths`：JSON 字符串数组。
- `weaknesses`：JSON 字符串数组。
- `role_gap_analysis`：岗位能力差距分析。
- `improvement_plan`：JSON 结构化训练计划数组。
- `next_practice_questions`：JSON 推荐练习题数组。
- `created_at`：UTC 创建时间。
- `updated_at`：UTC 更新时间。

约束：
- 一个 `interview_session` 只能有一份 `interview_report`。
- `session_id` 唯一。
- 各数值分数字段有数据库范围检查。

## interview_agent_events

保存 LangGraph Agent 的分支决策记录。

字段：
- `id`：UUID 字符串主键。
- `session_id`：关联 `interview_sessions.id`。
- `source_question_id`：触发本次决策的题目。
- `event_type`：`FOLLOW_UP_CREATED`、`NEXT_PRIMARY`、`READY_FOR_REPORT` 等事件类型。
- `decision`：`FOLLOW_UP`、`NEXT_PRIMARY`、`READY_FOR_REPORT`。
- `reason_summary`：LLM 或兜底逻辑给出的简要原因。
- `follow_up_question_id`：如果创建了追问，记录追问题目 ID。
- `created_at`：UTC 创建时间。

## 关系

- `users` 与 `interview_sessions` 是一对多。
- `interview_sessions` 与 `interview_questions` 是一对多。
- `interview_sessions.current_question_id` 指向当前 `interview_questions.id`。
- `interview_questions.parent_question_id` 自引用主问题。
- `interview_sessions` 与 `interview_answers` 是一对多。
- `interview_questions` 与 `interview_answers` 是一对一。
- `interview_answers` 与 `answer_evaluations` 是一对一。
- `interview_sessions` 与 `interview_reports` 是一对一。
- `interview_sessions` 与 `interview_agent_events` 是一对多。

## Alembic

当前迁移文件：

```text
backend/alembic/versions/6fba3a7c8156_create_users_and_interview_sessions.py
backend/alembic/versions/841c566025ec_add_interview_questions.py
backend/alembic/versions/5e616ec26249_add_interview_answers_and_evaluations.py
backend/alembic/versions/a17c0d9f4b12_add_interview_reports.py
backend/alembic/versions/b24e3a8f9c31_add_langgraph_follow_up_agent.py
```

执行迁移：

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```
## Phase 6A Analytics

Phase 6A does not add tables or Alembic migrations.

Analytics queries reuse:

- `interview_sessions` for owner, role, difficulty, type, and completion status.
- `interview_reports` for overall score, four ability scores, report time, and improvement plan.
- `interview_knowledge_base_links` plus `knowledge_bases` for displaying linked knowledge-base names in history.

Rows are included only when:

- `interview_sessions.user_id` matches the current authenticated user.
- `interview_sessions.status = COMPLETED`.
- A corresponding `interview_reports` row exists.

Raw answers, raw knowledge-base text, embeddings, prompt text, and secret
configuration values are not part of analytics responses.
