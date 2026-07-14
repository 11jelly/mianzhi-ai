# 阶段 2B 进度记录

日期：2026-06-22

## 目标

实现文本回答、单题 AI 评估、推进到下一题的闭环。

## 已完成

- 新增 `interview_answers` 表，保存用户对题目的文本回答。
- 新增 `answer_evaluations` 表，保存单题 AI 评分。
- 新增 Alembic 迁移 `5e616ec26249_add_interview_answers_and_evaluations.py`。
- 新增单题评分 Prompt，要求模型输出严格 JSON。
- 后端新增提交回答接口：`POST /api/v1/interviews/{session_id}/answers`。
- 后端新增回答历史接口：`GET /api/v1/interviews/{session_id}/answers`。
- 回答提交成功后推进 `current_question_index`。
- 最后一题完成后，会话状态进入 `READY_FOR_REPORT`。
- 前端会话详情页支持输入回答、提交评分、查看评分卡片和进入下一题。
- 自动化测试使用 Fake LLM，不调用真实百炼接口。

## 重要规则

- 只能回答当前题。
- 题目必须属于当前用户的当前会话。
- 每个题目只能回答一次。
- AI 评分成功后才写入回答与评分。
- AI 评分失败时不推进进度，不写入半成品数据。
- 回答长度最少 20 个字符，最多 5000 个字符。

## 真实联调缺陷修复：下一题展示错误

问题：
- 完成第 1 题并点击“进入下一题”后，页面仍显示第 1 题。
- 后端已将 `current_question_index` 推进到 1，但前端仍提交第 1 题 `question_id`。

根因：
- 前端详情页长期优先使用 `startMutation.data.current_question`，覆盖了 `GET current-question` 的新结果。

修复：
- 页面新增 `localCurrentQuestion`。
- 提交成功后将 `next_question` 写入 current-question 缓存。
- 点击“进入下一题”时优先使用 POST answers 响应里的 `next_question`。
- `GET current-question` 对完成态返回 `409`，不返回新题。

回归测试：
- 提交第 1 题后，`GET current-question` 返回 `sequence = 2`。
- 提交第 2 题后，`GET current-question` 返回 `sequence = 3`。
- 完成最后一题后，`GET current-question` 返回完成态错误。
- 已回答的第 1 题不能再次作为当前题提交。

## 真实联调缺陷修复：低质量回答评分 JSON 不稳定

问题：
- 用户输入大量重复“我不会”后，模型可能返回自然语言或不完整 JSON。
- 后端原逻辑直接暴露 `LLM 返回的评分 JSON 格式不合法。`。

根因：
- 评分 Prompt 没有充分约束低质量回答也必须返回 JSON。
- JSON 解析只支持纯 JSON 或完整 fenced JSON。
- 评分没有一次修复重试。
- Schema 强制 `strengths` 非空，不适合“完全无亮点”的低质量回答。

修复：
- Prompt 明确要求任何质量回答都必须评分，低质量回答给低分。
- 允许低质量回答 `strengths=[]`，但 `weaknesses` 必须非空。
- 支持纯 JSON、Markdown JSON 代码块、前后带少量说明文字的 JSON 对象提取。
- 第一次解析或校验失败时，使用同一题目、回答和评分标准重试一次 JSON 修复。
- 两次失败后返回友好提示：`AI 暂时无法完成本题评分，请稍后重试。当前回答未保存。`
- 失败时不保存回答、不保存评分、不推进进度。
- 兼容性归一化：
  - `strengths` / `weaknesses` 如果是单个字符串，转成单元素数组。
  - 四维分数合法但 `total_score` 不一致时，以四项之和作为 `total_score`。

新增测试：
- 低质量“我不会”回答 + Markdown JSON 低分结果可成功保存。
- 第一次返回自然语言、第二次返回合法 JSON，可重试成功。
- 四维分数合法但总分不一致时，自动归一化总分。
- 两次都非法时，不保存回答、不保存评分、不推进进度。
- 既有正常评分测试继续通过。

前端行为：
- 不直接展示“评分 JSON 格式不合法”。
- 展示友好错误：`AI 暂时无法完成本题评分，请稍后重试。当前回答未保存。`
- 提交失败后保留用户输入，用户可再次点击提交。

## 验证命令

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

前端：

```powershell
cd frontend
npm run build
```

## 未完成

- 阶段 2C：基于多题评分生成综合诊断报告。
- LangGraph 流程编排。
- 追问机制。
- 语音输入和语音识别。
- RAG 知识库。
- 虚拟人形象与实时交互。

## 建议提交信息

```text
fix: make answer evaluation robust for low-quality responses
```
