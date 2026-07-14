# 阶段 2C 进度记录

日期：2026-06-22

## 完成功能

- 新增 `interview_reports` 表与一对一报告模型。
- 新增综合报告 Prompt、Schema 和服务层。
- 新增 `POST /api/v1/interviews/{session_id}/report`。
- 新增 `GET /api/v1/interviews/{session_id}/report`。
- 后端确定性计算综合分和四维平均分，LLM 只生成文字诊断内容。
- 报告生成成功后，会话状态从 `READY_FOR_REPORT` 更新为 `COMPLETED`。
- 已完成会话重复生成报告时直接返回已有报告，不重复调用 LLM。
- 前端支持生成综合诊断报告。
- 前端使用 ECharts 原生 API 展示能力雷达图。
- 自动化测试使用 Fake LLM，不调用真实百炼 API。

## 本次真实联调修复

问题：
- 报告生成成功后，前端进入报告页时崩溃。
- 浏览器报错：`PromiseConstructor is not a constructor`。
- 堆栈来自 `echarts-for-react` 的 `componentDidMount` / `renderNewEcharts`。

根因：
- `echarts-for-react` 与当前 React/Vite/Rolldown 环境存在运行时兼容问题。
- 之前通过 `tslib` shim 解决了构建解析，但运行时 helper 仍不可靠。

修复：
- 移除 `echarts-for-react` 依赖。
- 删除 `tslib` shim 和 Vite alias。
- `AbilityRadarChart` 改用 ECharts 原生 API：
  - `useRef` 保存 DOM 容器。
  - `useEffect` 中 `echarts.init`。
  - `setOption` 设置 radar 图。
  - cleanup 中移除 resize 监听并 `chart.dispose()`。
  - 窗口 resize 时调用 `chart.resize()`。
- 雷达图容器固定高度 360px。
- 数据不存在或非法时显示空状态，不抛出异常。
- 路由增加 `errorElement`，避免单个组件异常显示默认错误页。

## 修改文件

- `frontend/src/components/AbilityRadarChart.tsx`
- `frontend/src/pages/RouteErrorPage.tsx`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/vite.config.ts`
- `frontend/package.json`
- `frontend/package-lock.json`
- `README.md`
- `docs/progress/phase-2c.md`

## 新增迁移文件

```text
backend/alembic/versions/a17c0d9f4b12_add_interview_reports.py
```

## 数据库升级命令与结果

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

结果：

```text
Running upgrade 5e616ec26249 -> a17c0d9f4b12, add_interview_reports
```

表验证：

```text
alembic_version
answer_evaluations
interview_answers
interview_questions
interview_reports
interview_sessions
users
```

## 分数聚合规则

- `overall_score`：所有单题 `total_score` 平均值，`ROUND_HALF_UP` 取整。
- `logic_score`：所有单题 `logic_score` 平均值，`ROUND_HALF_UP` 取整。
- `technical_score`：所有单题 `technical_score` 平均值，`ROUND_HALF_UP` 取整。
- `expression_score`：所有单题 `expression_score` 平均值，`ROUND_HALF_UP` 取整。
- `project_depth_score`：所有单题 `project_depth_score` 平均值，`ROUND_HALF_UP` 取整。

## 测试命令与结果

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

当前结果：
- `pytest`：39 passed
- `ruff check .`：All checks passed
- `npm run build`：通过

## 已知限制

- 本阶段不实现 LangGraph、追问、语音、RAG、虚拟人和历史趋势分析。
- 当前前端项目没有独立前端测试框架，本阶段未引入大型测试框架。
- Vite 提示 chunk 超过 500 kB，主要来自图表依赖，不影响功能。

## 手工验证路径

1. 启动前后端。
2. 打开一个已经 `COMPLETED` 且已有报告的会话。
3. 页面应正常展示报告，不再出现 `Unexpected Application Error!`。
4. 雷达图应显示四个维度：逻辑结构、技术准确性、表达清晰度、项目深度。
5. 刷新页面后报告和雷达图仍能恢复。
6. 如果报告四维数据缺失或非法，雷达图区域应显示“暂无有效能力数据”，页面不崩溃。

## 下一阶段建议

阶段 3 可以实现追问机制或语音输入，但仍应保持测试中不调用真实外部 API。

## 建议 Git commit message

```text
fix: render report radar chart with native echarts
```
