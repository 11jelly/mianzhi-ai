# Phase 10A：面智AI前端品牌升级与界面重构

## 完成功能

- 将前端品牌统一为“面智AI”。
- 新增原创 SVG 品牌标识，采用对话框、面试卡片和 AI 节点元素。
- 新增左侧固定导航栏、顶部轻量工具栏和右侧工作区。
- Dashboard 改为“我的面试”工作台，保留会话状态、进度、类型、难度、题量、知识库和继续/报告入口。
- 创建面试页改为分区表单，保留目标岗位、难度、面试类型、题目数量和知识库关联字段。
- 面试详情页改为桌面三栏布局，保留题目、浏览器朗读、本地虚拟面试官、讯飞云端数字人、录音、ASR、文本回答、提交评分、追问、报告生成和历史记录。
- 综合报告改为 Tabs 报告中心，保留综合分、四维能力、优点、短板、岗位差距、训练计划、推荐练习题和答题记录。
- 成长分析改为仪表盘布局，保留四项关键指标、能力雷达、成长趋势、岗位筛选、时间筛选、训练建议和历史面试列表。
- 知识库列表和详情改为左右分区，保留知识库创建、文档上传、文档状态、文档列表和检索测试。
- 增加统一视觉组件：`BrandMark`、`PageHeader`、`SectionCard`、`MetricCard`、`StatusBadge`、`EmptyState`、`PrimaryButton`、`SecondaryButton`。
- 更新 README 和架构文档，修复旧阶段描述。
- 回归修复：移除侧栏重复“面试记录”导航入口，“我的面试”统一承担全部会话列表、未完成恢复和已完成报告入口。
- 回归修复：移除顶部工具栏重复的“知识库”和“创建面试”快捷按钮，入口保留在左侧导航和 Dashboard 主按钮中。
- 回归修复：调整 AppShell 滚动策略，主工作区恢复 `overflow-y: auto`，长报告、知识库列表、历史表格继续使用局部滚动。
- 回归修复：恢复 8A 本地虚拟面试官五种状态的可见视觉反馈，保持状态来源和优先级不变。
- 第二轮优化：Dashboard 会话卡片改用 300px 起步的自适应网格，核心字段允许换行并使用 `overflow-wrap`，避免岗位、类型、难度、题量和知识库名称被省略号截断。
- 第二轮优化：成长分析页移除右上角和空状态中的重复“创建面试”入口。
- 第二轮优化：创建面试页按“目标岗位/面试类型、难度/题量、知识库、增强说明、底部操作”重新排布，难度与题量各占半行。
- 第二轮优化：题目生成阶段仍使用 THINKING 视觉，但本地虚拟面试官展示“正在准备本轮面试题”，与 ASR、评分、追问和报告阶段的“正在分析”区分。
- 第二轮优化：进行中面试详情改为双栏工作台，左侧承载题目、作答、录音和已完成回答，右侧优先展示云端数字人舞台、本地状态卡、进度和 Agent 决策。
- 第二轮优化：云端数字人未启用时保留较大 16:9 舞台和启用说明，本地虚拟面试官保持横向紧凑状态卡，窄屏降级为单列。

## 修改文件

- `README.md`
- `docs/architecture.md`
- `docs/progress/phase-10a-ui-redesign.md`
- `frontend/src/index.css`
- `frontend/src/App.tsx`
- `frontend/src/components/ui.tsx`
- `frontend/src/components/InterviewReport.tsx`
- `frontend/src/components/VirtualInterviewer.tsx`
- `frontend/src/components/VirtualInterviewer.module.css`
- `frontend/src/components/XfyunAvatarPanel.tsx`
- `frontend/src/components/XfyunAvatarPanel.module.css`
- `frontend/src/pages/AppLayout.tsx`
- `frontend/src/pages/AuthShell.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/NewInterviewPage.tsx`
- `frontend/src/pages/InterviewDetailPage.tsx`
- `frontend/src/pages/GrowthAnalyticsPage.tsx`
- `frontend/src/pages/KnowledgeBasePage.tsx`
- `frontend/src/pages/KnowledgeBaseDetailPage.tsx`

## 保留的页面与路由

- `/login`
- `/register`
- `/dashboard`
- `/interviews/new`
- `/interviews/:sessionId`
- `/growth`
- `/knowledge-bases`
- `/knowledge-bases/:knowledgeBaseId`

当前项目没有独立“面试记录”页面。回归修复后，侧边栏不再显示重复的“面试记录”入口；如直接访问 `/interviews`，会重定向到 `/dashboard` 以复用“我的面试”页面。

## 回归修复说明

- 移除重复的面试记录导航入口，避免“我的面试”和“面试记录”同时高亮。
- “我的面试”页面继续查询并展示当前用户面试会话，覆盖 `CREATED`、`IN_PROGRESS`、`READY_FOR_REPORT` 和 `COMPLETED` 状态。
- 顶部工具栏不再显示“知识库”和“创建面试”按钮；知识库入口保留在侧栏，创建面试入口保留在侧栏和 Dashboard 主按钮。
- AppShell 桌面端保持固定侧栏和稳定顶部栏，主内容区使用纵向滚动；移动端允许自然页面滚动。
- Dashboard 会话卡片改为更紧凑的自适应网格，保留岗位、状态、进度、类型、难度、题量、知识库和操作按钮。
- 8A 本地虚拟面试官仍使用 `useInterviewerState` 的真实状态，恢复 `IDLE`、`SPEAKING`、`LISTENING`、`THINKING`、`COMPLETED` 的视觉区分。
- 本次未修改后端、接口、数据库、RAG、LangGraph、ASR、评分、报告、讯飞数字人 hook 或播放中断业务逻辑。

## 第二轮界面优化说明

- Dashboard 卡片完整展示策略：卡片网格使用 `repeat(auto-fit, minmax(300px, 1fr))`，核心业务字段不使用省略号，长岗位、长知识库名和类型/难度值允许自然换行。
- 成长分析去重：页面标题区和空状态不再提供“创建面试”按钮，创建入口仅保留在左侧导航和“我的面试”页面。
- 创建面试布局：第一行目标岗位与面试类型，第二行难度与题目数量，第三行知识库整行，第四行增强说明整行，底部取消与创建按钮右对齐。
- 状态文案区分：`startMutation.isPending && !currentQuestion` 时向本地虚拟面试官传入展示文案“正在准备本轮面试题”；ASR、评分、追问决策和报告生成仍使用原 THINKING 状态文案“AI 面试官正在分析”。
- 面试详情布局：进行中会话在桌面端采用左侧主工作区和右侧面试官舞台；小于约 1200px 时降级为单列，避免文字挤压和横向滚动。

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

前端：

```powershell
cd frontend
npm run build
```

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## 测试结果

- `npm run build`：第二轮优化后通过。Vite 提示部分 chunk 超过 500 kB；不影响构建成功。
- `python -m pytest`：项目虚拟环境普通沙箱内因 `_sqlite3` DLL 访问被拒绝失败；提升权限重跑通过，`72 passed, 2 warnings`。
- `python -m ruff check .`：第二轮优化后通过，`All checks passed!`。

## 手工测试清单

本次未启动完整本地服务和浏览器做手工联调。以下清单保留为阶段 10A 的必测路径，需在具备数据库、浏览器麦克风权限和外部服务配置的本机环境执行。

- 登录 / 注册。
- Dashboard。
- 创建面试。
- 我的面试会话列表。
- 未完成会话恢复。
- 面试详情。
- 浏览器朗读。
- 录音与 ASR。
- 提交回答。
- LangGraph 追问。
- 报告生成。
- 报告查看。
- 成长分析。
- 岗位筛选。
- 知识库。
- 云端数字人开启与关闭。
- `COMPLETED` 会话展示。
- 退出登录。

## 已知限制

- 本阶段未引入前端测试框架，前端以 TypeScript/Vite build 做静态回归。
- 报告“回答证据高亮”尚未实现，页面只展示真实题目、回答和评分记录，并明确标注后续版本提供。
- 讯飞云端数字人仍是本地演示试用层，不是生产虚拟人服务。
- 手工测试需要本地后端、数据库、浏览器麦克风权限和可用的外部服务配置。

## 下一步建议

- 为核心页面补充前端组件测试或 Playwright 冒烟测试。
- 对报告中心增加真实回答证据高亮能力。
- 对 Dashboard 增加分页或状态筛选。
- 对知识库详情增加文档处理失败的重试入口。

## 建议 Git commit message

```text
feat(frontend): redesign ui for mianzhi ai workspace
```

## 进行中面试详情三栏布局修复

- 完成功能：将 `IN_PROGRESS` 面试详情页从左右两栏调整为桌面端三栏工作台：左栏“面试官舞台”、中栏“当前题目与回答区”、右栏“面试控制台”。
- 完成功能：云端讯飞数字人与本地虚拟面试官合并到同一个“面试官舞台”卡片中；云端区域保持 16:9 舞台，占左栏主要面积，本地虚拟面试官保持横向状态卡。
- 完成功能：将“当前状态 / 题目进度 / Agent 决策”合并到“面试控制台”卡片的 Tabs 中，避免右侧纵向堆叠成一长串卡片。
- 完成功能：“已完成回答”移动到三栏工作台下方，作为全宽卡片展示，并继续使用局部滚动承载较多历史回答。
- 完成功能：`<1200px` 时自动降级为单列，顺序为当前题目与回答、面试官舞台、面试控制台、已完成回答；1280px 左右桌面宽度下使用压缩三栏宽度，避免横向溢出。
- 修改文件：`frontend/src/pages/InterviewDetailPage.tsx`、`frontend/src/index.css`、`frontend/src/components/XfyunAvatarPanel.tsx`、`frontend/src/components/XfyunAvatarPanel.module.css`、`frontend/src/components/AgentEventTimeline.tsx`、`frontend/src/components/VirtualInterviewer.module.css`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改后端、数据库、Alembic、接口参数、`useXfyunAvatar.ts`、`stopQuestionPlayback`、浏览器 TTS、录音、ASR、评分、LangGraph、RAG、报告生成或虚拟人生命周期业务逻辑。
- 测试结果：`npm run build` 通过；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过。
- 已知限制：本次未启动浏览器做 Playwright 截图校验，桌面和窄屏布局仍需在本地真实数据与数字人配置下手工确认。
- 建议 Git commit message：`fix(frontend): balance active interview detail workspace`

## 第三轮前端布局与状态展示修复

- 完成功能：收紧进行中面试页左侧云端数字人舞台高度，桌面端使用受控 16:9 舞台，避免本地虚拟面试官落到 1440×900 首屏之外。
- 完成功能：本地虚拟面试官增加紧凑展示模式，保持横向布局和完整状态文案，首屏可同时看到云端舞台、本地状态、当前题目、回答录音区和控制台。
- 完成功能：修复已有 `IN_PROGRESS` 会话进入时因 `currentQuestionQuery.isFetching` 被计入 THINKING 而误显示“正在分析”的问题；已有题目加载完成时默认回到 `IDLE`，展示“AI 面试官已就绪”。
- 完成功能：题目生成阶段继续使用 THINKING 视觉，但展示“正在准备本轮面试题”；ASR、评分、追问决策和报告生成阶段才展示分析状态。
- 完成功能：云端数字人操作区固定为两行按钮；录音区固定为录音控制、删除与计时、整行提交按钮三层结构，避免桌面端随机换行。
- 完成功能：知识库列表与新建知识库两张主卡片在桌面端等高，列表多时在卡片内部滚动；窄屏恢复自然单列高度。
- 完成功能：报告总览中“优势”和“待提升能力”改为等高 Grid 卡片，保留全部优点、短板、岗位差距与训练计划内容。
- 修改文件：`frontend/src/pages/InterviewDetailPage.tsx`、`frontend/src/components/VirtualInterviewer.tsx`、`frontend/src/components/VirtualInterviewer.module.css`、`frontend/src/components/XfyunAvatarPanel.tsx`、`frontend/src/components/XfyunAvatarPanel.module.css`、`frontend/src/components/VoiceAnswerRecorder.tsx`、`frontend/src/components/InterviewReport.tsx`、`frontend/src/index.css`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改后端、数据库、Alembic、接口参数、RAG、LangGraph、ASR、报告、会话恢复、讯飞 SDK、`useXfyunAvatar.ts`、`stopQuestionPlayback`、环境变量或密钥。
- 测试结果：`npm run build` 通过；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过。
- 已知限制：未启动浏览器执行真实 1440×900 截图核验，仍建议在本机以真实会话数据手工确认首屏和窄屏效果。
- 建议 Git commit message：`fix(frontend): polish active interview layout and status display`

## 第四轮过程页展示边界修复

- 完成功能：从 `CREATED` 和 `IN_PROGRESS` 面试过程页删除“已完成回答”前端展示模块，不保留空状态或底部大卡片；回答数据、评分、追问、报告和恢复逻辑不变。
- 完成功能：`CREATED` 会话详情改为两栏布局，左栏为“本地面试官与开始区域”，包含本地虚拟面试官、未开始提示和“开始文本面试”按钮；右栏为云端数字人舞台。
- 完成功能：`IN_PROGRESS` 会话继续使用三栏布局，比例调整为左窄、中宽、右窄，左栏面试官舞台、中栏当前题目与回答输入、右栏面试控制台。
- 完成功能：三栏外层使用同一 CSS Grid 行，列容器和主卡片使用 `height: 100%`、`min-height: 0`、`display: flex`，让左中右外边界底部对齐；中栏和右栏内容超出时在内部滚动。
- 完成功能：`<1200px` 时 `IN_PROGRESS` 顺序为当前题目与回答、面试官舞台、面试控制台；`CREATED` 顺序为本地面试官与开始区域、云端数字人舞台。
- 修改文件：`frontend/src/pages/InterviewDetailPage.tsx`、`frontend/src/index.css`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改后端、数据库、Alembic、接口、RAG、LangGraph、ASR、评分、报告生成、会话恢复、讯飞 SDK、`useXfyunAvatar.ts`、`stopQuestionPlayback`、环境变量或密钥。
- 测试结果：`npm run build` 通过；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过。
- 已知限制：未启动浏览器做 1440×900 视觉截图核验，仍建议用真实 CREATED、IN_PROGRESS、COMPLETED 会话手工检查布局和功能。
- 建议 Git commit message：`fix(frontend): refine interview process page layout`

## 第五轮数字人与评分态回归修复

- 完成功能：修复 `CREATED` 页面已启用云端数字人后点击“开始文本面试”，进入 `IN_PROGRESS` 时舞台 DOM 切换导致视频不显示的问题；前端 hook 现在区分用户期望启用、SDK 实例连接和舞台挂载，并在舞台 DOM 变化后自动重连。
- 完成功能：云端数字人启用或自动重连不再把本地虚拟面试官推入 THINKING；本地状态仍按 `COMPLETED > THINKING > LISTENING > SPEAKING > IDLE` 优先级派生。
- 完成功能：云端数字人操作按钮改为短文案两行布局：启用/关闭、朗读/中断；按钮增加 `title`/Tooltip 和溢出保护，避免左栏文字溢出。
- 完成功能：提交回答后保留“回答与语音输入”卡片和本题已提交文本，禁用文本框、录音、ASR 和提交按钮，并在中栏继续显示 `AI 单题评分反馈`，不恢复“已完成回答”模块。
- 修改文件：`frontend/src/hooks/useXfyunAvatar.ts`、`frontend/src/components/XfyunAvatarPanel.tsx`、`frontend/src/components/XfyunAvatarPanel.module.css`、`frontend/src/pages/InterviewDetailPage.tsx`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改后端、数据库、Alembic、接口、RAG、LangGraph、ASR、评分算法、报告生成、环境变量或真实密钥；未删除回答数据、评分数据、追问数据、云端数字人、本地虚拟面试官、浏览器朗读、录音、ASR、提交评分、会话恢复或报告功能。
- 测试结果：`npm run build` 通过；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过。
- 已知限制：未启动真实浏览器和讯飞数字人服务做端到端视频流观察，仍需在本机按 CREATED → 启用数字人 → 开始面试 → IN_PROGRESS 的路径手工验证画面恢复。
- 建议 Git commit message：`fix(frontend): restore avatar and answer feedback states`

## 第六轮单题评分反馈布局修复

- 完成功能：将 `AI 单题评分反馈` 从中栏答题区域中移出，改为 `.interview-workspace` 三栏工作台之后的全宽同级区域，避免评分反馈高度把左侧面试官舞台和右侧面试控制台同步拉长。
- 完成功能：三栏工作台只保留三个直接子模块：左栏面试官舞台、中栏当前题目与回答输入、右栏面试控制台；评分反馈与后续下一题提示位于三栏下方。
- 完成功能：评分期间中栏继续保留回答与语音输入卡片，显示本题已提交内容，并通过既有 `answerLocked` 逻辑禁用文本输入、录音、ASR 和提交按钮，防止重复提交。
- 完成功能：调整三栏 CSS 为自然高度对齐，`.interview-workspace` 使用 `align-items: start`，三栏列容器和主卡片不再用评分反馈高度撑开；`.single-question-feedback` 独立占满主内容宽度。
- 修改文件：`frontend/src/pages/InterviewDetailPage.tsx`、`frontend/src/index.css`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改后端、数据库、Alembic、接口、回答数据、评分数据、LangGraph 追问、ASR、录音、浏览器朗读、讯飞数字人 SDK、虚拟人生命周期、题目切换或报告生成逻辑；未恢复 `CREATED` / `IN_PROGRESS` 过程页的“已完成回答”模块。
- 测试结果：`npm run build` 通过，Vite 仍提示部分 chunk 超过 500 kB；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过，结果为 `All checks passed!`。
- 已知限制：未启动浏览器执行真实 1440×900 / 1280×800 截图校验，仍建议用真实进行中会话手工确认提交答案后的三栏与评分反馈位置。
- 建议 Git commit message：`fix(frontend): separate question feedback from interview workbench`

## 第七轮单题评分后三栏等高修复

- 完成功能：在 `AI 单题评分反馈` 已经位于三栏下方全宽区域的基础上，恢复上方 `.interview-workspace` 三栏工作台同一 Grid 行内的等高拉伸，修复评分后左侧面试官舞台、右侧面试控制台短于中栏造成的外部留白。
- 完成功能：`.interview-workspace` 使用 `align-items: stretch`；`.interview-stage-column`、`.interview-answer-column`、`.interview-console-column` 使用 `height: 100%` 和纵向 flex；左右两张主卡片 `.interviewer-stage-card`、`.interview-console-card` 使用 `height: 100%`，仅拉齐外框底边，内部内容仍保持顶部对齐。
- 完成功能：`<1180px` 单列布局下覆盖为自然高度和 `align-items: start`，避免窄屏被桌面等高规则强制拉伸。
- 修改文件：`frontend/src/index.css`、`docs/progress/phase-10a-ui-redesign.md`。
- 兼容原则：未修改 `InterviewDetailPage` 组件层级，`AI 单题评分反馈` 仍是 `.interview-workspace` 之后的全宽同级模块；未修改后端、数据库、接口、评分、LangGraph、ASR、录音、云端数字人、本地虚拟面试官状态逻辑、环境变量或密钥；未恢复“已完成回答”模块。
- 测试结果：`npm run build` 通过，Vite 仍提示部分 chunk 超过 500 kB；普通沙箱下 `python -m pytest` 因 `_sqlite3` DLL 权限失败，提升权限重跑通过，结果为 `72 passed, 2 warnings`；`python -m ruff check .` 通过，结果为 `All checks passed!`。
- 已知限制：未启动浏览器执行真实 1440×900 / 1280×800 视觉校验，仍建议在真实进行中会话中手工确认评分反馈出现后三栏底部齐平。
- 建议 Git commit message：`fix(frontend): align interview workbench columns after feedback`
