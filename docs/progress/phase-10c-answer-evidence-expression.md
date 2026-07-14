# Phase 10C：回答证据高亮与表达质量辅助分析

## 完成功能

- 在单题评分结果中新增回答证据字段，支持优势证据和待改进证据。
- 服务端校验每条证据的 `quote`，只保留来自用户原始回答的连续原文片段。
- 新增表达质量辅助分析，基于回答文本计算长度、句子数、平均句长、填充词、重复提示和结构表达信号。
- 支持在用户通过录音转写作答并提交有效录音秒数时估算语速。
- 报告接口新增 `answer_evidence` 和 `expression_analysis` 可选结构，旧字段不删除、不重命名。
- 报告页新增“回答证据”和“表达质量”展示，回答原文中的证据 quote 会被高亮。
- 保持四维评分范围、评分持久化、报告生成、RAG、Resume-RAG、LangGraph、ASR 和虚拟人生命周期不变。

## 修改文件

- `README.md`
- `docs/architecture.md`
- `docs/progress/phase-10c-answer-evidence-expression.md`
- `backend/alembic/versions/e9c7a1f3b5d2_add_answer_evidence_expression.py`
- `backend/app/models/answer_evaluation.py`
- `backend/app/models/interview_answer.py`
- `backend/app/prompts/answer_evaluation.py`
- `backend/app/schemas/answer.py`
- `backend/app/schemas/evaluation.py`
- `backend/app/schemas/report.py`
- `backend/app/services/evaluation_service.py`
- `backend/app/services/expression_analysis.py`
- `backend/app/services/llm_client.py`
- `backend/app/services/report_service.py`
- `backend/tests/test_phase10c_answer_evidence_expression.py`
- `frontend/src/api/types.ts`
- `frontend/src/components/InterviewReport.tsx`
- `frontend/src/components/VoiceAnswerRecorder.tsx`
- `frontend/src/index.css`
- `frontend/src/pages/InterviewDetailPage.tsx`

## 新增数据库字段

Alembic revision：`e9c7a1f3b5d2_add_answer_evidence_expression`

- `interview_answers.recording_duration_seconds`：可空浮点数，保存本次回答来自录音转写时的录音秒数。
- `answer_evaluations.evidence_items_json`：可空 JSON，保存通过服务端校验后的证据项。
- `answer_evaluations.expression_metrics_json`：可空 JSON，保存表达质量辅助指标。

所有字段均允许为空，旧会话和旧评分记录无需回填。

## 回答证据数据流

```text
用户提交回答
  -> LLM 单题评分返回原有分数与反馈
  -> LLM 可选返回 evidence_items
  -> 服务端逐条校验 quote
  -> 无效证据丢弃，有效证据写入 answer_evaluations.evidence_items_json
  -> 报告接口按题目返回 answer_evidence
  -> 前端报告页高亮原回答中的 quote
```

## quote 服务端校验策略

- `dimension` 必须是 `logic`、`technical`、`expression`、`project_depth`。
- `polarity` 必须是 `strength` 或 `improvement`。
- `quote` 必须非空、最长 80 个字符，并且是原始回答中的连续子串。
- `quote` 不能是“无”“暂无”等占位文本。
- 明显邮箱或手机号片段会被丢弃，避免在证据区域突出隐私信息。
- 每题最多保留 6 条证据。
- 证据校验失败不影响单题评分成功，全部无效时保存空数组。

## 表达质量指标定义

- `character_count`：中文字符数加英文/数字词数量的近似有效长度。
- `sentence_count`：按中英文句末符号、分号和换行拆分的句子数。
- `average_sentence_length`：有效长度除以句子数。
- `filler_word_count`：统计“嗯、啊、呃、那个、就是、然后、其实、怎么说、对吧”等填充词。
- `filler_word_rate`：填充词数量除以有效长度。
- `repetition_hint`：当同一表达重复出现时给出提示。
- `structure_signal_count`：统计“首先、其次、最后、第一、第二、第三、因为、所以、例如、总结”等结构信号。
- `estimated_speech_rate`：仅在有有效录音秒数时，按有效字词数量 / 分钟估算。

表达质量分析是辅助诊断，不改变四维评分，不做情绪、口音、声纹或人格判断。

## 录音时长的作用与限制

- 前端录音转写成功后，从 ASR 响应或本地计时中取得秒数，并随回答提交。
- 手动输入文本时不提交录音秒数，报告页显示语速不可用或样本不足。
- 后端拒绝负数或超过当前 ASR 最大时长配置的录音秒数。
- 语速仅为基于转写文本和录音时长的估算，不代表真实语音声学质量。

## 与既有能力的关系

- 原四维评分范围和聚合规则保持不变。
- RAG 与 Resume-RAG 仍只作为题目生成、评分或报告上下文，不作为用户原话证据来源。
- LangGraph 追问状态机、ASR 转写、报告生成和虚拟人生命周期不变。
- 进行中面试页不恢复“已完成回答”模块；证据与表达质量只在报告页或结果查看区域展示。

## 旧会话兼容策略

- 旧评分记录没有 `evidence_items_json` 时，报告页显示无可靠证据空状态。
- 旧评分记录没有 `expression_metrics_json` 时，表达质量显示样本不足。
- 旧回答没有 `recording_duration_seconds` 时，不估算语速。
- 报告接口新增字段为可选结构，不删除、不重命名原有响应字段。

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
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .

cd frontend
npm run build
```

## 测试结果

- `python -m alembic upgrade head`：通过，执行 `d4f0b7a2c91e -> e9c7a1f3b5d2`。
- `python -m alembic current`：通过，当前为 `e9c7a1f3b5d2 (head)`。
- `python -m alembic heads`：通过，head 为 `e9c7a1f3b5d2`。
- `python -m pytest tests\test_phase10c_answer_evidence_expression.py`：通过，`11 passed, 2 warnings`。
- `python -m pytest`：通过，`94 passed, 2 warnings`。
- `python -m ruff check .`：通过，`All checks passed!`。
- `npm run build`：通过；Vite 仍提示部分 chunk 超过 500 kB。

## 手工测试清单

1. 完成一场面试并生成报告。
2. 打开报告总览，确认原有分数、优势、短板、岗位差距和训练计划仍显示。
3. 打开“回答证据”，确认按题目展示问题、回答原文、优势证据和待改进证据。
4. 确认证据高亮内容均来自回答原文，且无证据时显示空状态。
5. 打开“表达质量”，确认长度、句子、填充词、结构信号和重复提示正常。
6. 手动输入回答时，确认语速显示不可用或样本不足。
7. 录音转写回答并提交后，确认报告页可显示估算语速。
8. 窄屏查看报告页，确认高亮文本不截断、不横向溢出。
9. 验证进行中面试三栏工作台没有恢复“已完成回答”模块。
10. 验证 RAG、Resume-RAG、LangGraph、ASR、评分、报告和虚拟人流程不回归。

## 已知限制

- 证据高亮只基于模型返回并通过服务端校验的 quote，不主动从评分文本中反推证据。
- 重复表达、填充词和结构信号采用轻量规则统计，不等同于语言学精细分析。
- 估算语速依赖前端提交的录音秒数和转写文本，不分析音色、停顿、口音或声纹。

## 下一步建议

- 后续可为报告页增加前端自动化截图回归。
- 后续可增加更多行业化表达结构信号词，但需保持辅助诊断边界。

## 建议 Git commit message

```text
feat(report): add answer evidence and expression analysis
```
