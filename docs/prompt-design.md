# Prompt 设计

当前包含四类 Prompt：面试题生成 Prompt、单题回答评分 Prompt、追问决策 Prompt、综合诊断报告 Prompt。

阶段 4A 的 ASR 转写不使用 Prompt，不改变评分、追问或报告 Prompt。浏览器录音仅用于把语音转成可编辑文本，用户确认后仍走原有文本回答评分流程。

## 分数计算规则

综合报告中的数值分数不允许由 LLM 随意生成，必须由后端根据该会话全部 `PRIMARY` 主问题的 `answer_evaluations` 记录计算：

```text
overall_score = 所有 total_score 的平均值，四舍五入为整数
logic_score = 所有 logic_score 的平均值，四舍五入为整数
technical_score = 所有 technical_score 的平均值，四舍五入为整数
expression_score = 所有 expression_score 的平均值，四舍五入为整数
project_depth_score = 所有 project_depth_score 的平均值，四舍五入为整数
```

四舍五入使用明确的 `ROUND_HALF_UP` 策略。`FOLLOW_UP` 追问只作为补充上下文进入报告 Prompt，不参与平均分。前端雷达图直接使用后端返回的四维分数。

## 追问决策 Prompt

输入包含：
- 会话目标岗位、难度、面试类型。
- 当前主问题题干。
- 用户回答。
- 单题评分结果和反馈。
- 当前会话追问上限与已追问数量。

输出必须是严格 JSON：

```json
{
  "should_follow_up": true,
  "follow_up_category": "技术细节追问",
  "follow_up_question": "请进一步说明这个方案在异常场景下如何保证一致性？",
  "reason_summary": "回答提到了方案方向，但缺少关键边界条件。"
}
```

规则：
- 只允许 `PRIMARY` 主问题触发追问。
- `FOLLOW_UP` 不会继续触发追问。
- 每道主问题最多 1 道追问。
- 每个会话最多 `MAX_FOLLOW_UPS_PER_SESSION` 道追问。
- 0 分、明显“不会”、重复空洞或完全跑题时不强制追问。
- 中低分且有部分技术内容但关键细节缺失时，可以追问。
- `should_follow_up = false` 时，`follow_up_question` 可以为空字符串。
- 所有文本使用简体中文。

## 综合诊断报告 Prompt

输入包含：
- 目标岗位。
- 面试难度。
- 面试类型。
- 后端确定性计算出的总体分数和四维分数。
- 每一道题的题目、题目类型、用户回答、单题评分、优点、待改进点和反馈。
- `FOLLOW_UP` 追问记录作为上下文帮助诊断，但不得影响数值分数。

LLM 只返回文字诊断字段，不返回任何分数字段：

```json
{
  "summary": "本次面试整体表现……",
  "strengths": ["优势 1", "优势 2"],
  "weaknesses": ["待提升点 1", "待提升点 2"],
  "role_gap_analysis": "与目标岗位要求相比……",
  "improvement_plan": [
    {
      "priority": 1,
      "topic": "MySQL 索引与慢查询优化",
      "reason": "单题回答中缺少 EXPLAIN 与索引失效分析。",
      "actions": ["练习联合索引设计", "完成三组 EXPLAIN 分析案例"],
      "expected_outcome": "能够清晰说明索引设计与慢查询优化路径。"
    }
  ],
  "next_practice_questions": ["请说明 Redis 缓存击穿治理方案。"]
}
```

要求：
- 输出必须是严格 JSON。
- 所有文本使用简体中文。
- `strengths`、`weaknesses`、`next_practice_questions` 必须是字符串数组。
- `improvement_plan` 必须是结构化数组。
- 用户回答低分、空洞或“不会”时仍能生成正式报告。
- 如果模型返回分数字段，后端校验失败并重试一次。

## JSON 解析与失败策略

后端支持：
- 纯 JSON 对象。
- Markdown JSON 代码块。
- JSON 前后带少量说明文字时，提取 JSON 对象。

第一次输出无法解析或 Pydantic 校验失败时，后端会发起一次修复重试。第二次仍失败：
- 不写入 report。
- session 保持 `READY_FOR_REPORT`。
- 前端显示友好错误。
- 不改变已有单题回答与评分。
