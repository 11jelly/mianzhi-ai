# API 设计

基础地址：

```text
http://127.0.0.1:8000
```

除注册、登录和健康检查外，业务接口都需要：

```text
Authorization: Bearer <token>
```

## 面试会话

```text
POST /api/v1/interviews
GET  /api/v1/interviews?page=1&page_size=10
GET  /api/v1/interviews/{session_id}
POST /api/v1/interviews/{session_id}/start
GET  /api/v1/interviews/{session_id}/current-question
GET  /api/v1/interviews/{session_id}/questions
POST /api/v1/interviews/{session_id}/answers
GET  /api/v1/interviews/{session_id}/answers
GET  /api/v1/interviews/{session_id}/agent-events
```

### GET /current-question

业务规则：
- `IN_PROGRESS` 时返回当前可作答题目。
- 优先使用 `interview_sessions.current_question_id`。
- 老会话没有 `current_question_id` 时回退到 `current_question_index + 1` 对应的主问题。
- `READY_FOR_REPORT` 和 `COMPLETED` 不返回新题目，返回业务错误。

### POST /answers

阶段 3A 响应增加 Agent 决策字段：

```json
{
  "answer": {},
  "evaluation": {},
  "session_status": "IN_PROGRESS",
  "answered_question_count": 1,
  "question_count": 3,
  "next_question": {
    "id": "uuid",
    "question_type": "FOLLOW_UP",
    "parent_question_id": "primary-question-id"
  },
  "agent_action": "FOLLOW_UP",
  "agent_reason_summary": "回答有部分技术内容，但关键细节不足。"
}
```

`agent_action` 取值：
- `FOLLOW_UP`：后端已创建追问题，并将其设为当前题。
- `NEXT_PRIMARY`：进入下一道主问题。
- `READY_FOR_REPORT`：全部主问题和追问完成。

规则：
- 前端应优先使用 `next_question` 展示下一题。
- `next_question = null` 且 `session_status = READY_FOR_REPORT` 时展示报告生成入口。
- 提交非当前题返回 `409 This is not the current question.`。

### GET /agent-events

返回当前会话的 Agent 决策事件：

```json
[
  {
    "id": "uuid",
    "session_id": "uuid",
    "source_question_id": "uuid",
    "event_type": "FOLLOW_UP_CREATED",
    "decision": "FOLLOW_UP",
    "reason_summary": "回答有部分技术内容，但关键细节不足。",
    "follow_up_question_id": "uuid",
    "created_at": "2026-06-22T00:00:00"
  }
]
```

只允许读取当前用户自己的会话事件。

## 综合诊断报告

```text
POST /api/v1/interviews/{session_id}/report
GET  /api/v1/interviews/{session_id}/report
```

### POST /report

业务规则：
- 校验会话属于当前用户，否则返回 `404`。
- 只有 `READY_FOR_REPORT` 或已有报告的 `COMPLETED` 会话可调用。
- `READY_FOR_REPORT` 时，后端读取全部题目、回答和单题评分。
- 主问题回答数和主问题评分数必须等于 `question_count`。
- 数值分数由后端确定性计算，不由 LLM 生成。
- 数值分只聚合 `PRIMARY` 题目，`FOLLOW_UP` 题目作为补充材料传入 Prompt。
- LLM 只生成文字诊断内容。
- 写入报告和更新会话为 `COMPLETED` 在同一次事务中完成。
- 已有报告时直接返回，不重复调用 LLM。
- LLM 失败时不写入报告，会话保持 `READY_FOR_REPORT`。

响应字段：

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "overall_score": 78,
  "logic_score": 20,
  "technical_score": 24,
  "expression_score": 16,
  "project_depth_score": 18,
  "summary": "本次面试整体表现……",
  "strengths": ["优势"],
  "weaknesses": ["待提升点"],
  "role_gap_analysis": "岗位差距分析",
  "improvement_plan": [
    {
      "priority": 1,
      "topic": "训练主题",
      "reason": "原因",
      "actions": ["行动"],
      "expected_outcome": "预期结果"
    }
  ],
  "next_practice_questions": ["练习题"],
  "created_at": "2026-06-22T00:00:00",
  "updated_at": "2026-06-22T00:00:00"
}
```

### GET /report

业务规则：
- 校验当前用户归属。
- 未生成报告时返回 `404`。
- 只返回公开报告数据，不返回 `expected_points`、LLM 配置或敏感信息。

## 错误提示

报告生成 LLM 两次输出都不合法时返回：

```text
AI 暂时无法生成综合诊断报告，请稍后重试。
```

## 语音转写

```text
POST /api/v1/speech/transcriptions
```

业务规则：
- 需要 `Authorization: Bearer <token>`。
- 请求类型为 `multipart/form-data`。
- 文件字段名为 `audio`。
- 可选表单字段：`duration_seconds`。
- 只接受 WAV 文件。
- 文件大小不得超过 `ASR_MAX_FILE_SIZE_MB`。
- `duration_seconds` 不得超过 `ASR_MAX_DURATION_SECONDS`。
- 接口只负责转写，不创建回答、不创建评分、不推进面试状态。
- 原始音频只写入系统临时目录，调用结束后立即删除，不写入 MySQL。

成功响应：

```json
{
  "text": "转写后的回答文本",
  "model": "qwen3-asr-flash",
  "duration_seconds": 18.5
}
```

错误：
- `401`：未登录。
- `413`：文件过大。
- `422`：格式错误、空音频或时长超过限制。
- `503`：ASR 未配置或 SDK 不可用。
- `502`：云端 ASR 调用失败。
## Growth Analytics

All analytics endpoints require JWT authentication and only read the current user's data.
They never return raw answers, knowledge-base document text, embeddings, prompts, or secrets.

```text
GET /api/v1/analytics/overview
GET /api/v1/analytics/trend?days=90&target_role=Python Backend
GET /api/v1/analytics/history?page=1&page_size=10&target_role=Python Backend
```

Aggregation rules:

- Include only `interview_sessions.status = COMPLETED`.
- Include only sessions with a matching `interview_reports` row.
- Use `interview_reports.created_at` for trend time.
- `weakest_dimension` is computed from the latest up to 5 reports by four-dimension averages.
- `history` includes linked knowledge-base names only, not document content.
