# 面智AI — AI产品经理智能面试训练平台

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20.19%2B-brightgreen)](https://nodejs.org/)
[![React](https://img.shields.io/badge/react-19-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.138-009688)](https://fastapi.tiangolo.com/)

面向**AI产品经理**岗位的智能面试训练平台。通过 AI 驱动的出题、评分、追问和诊断，帮助产品经理候选人系统化提升面试能力。

---

## ✨ 核心功能

| 模块 | 功能 |
|---|---|
| 🤖 **AI 智能出题** | 基于岗位+难度+类型自动生成面试题，支持产品思维、数据分析、用户研究、A/B测试、PRD撰写等产品面试场景 |
| 📊 **四维能力评分** | 逻辑结构 · 专业深度 · 表达清晰度 · 落地深度，每题独立评分 |
| 🔄 **LangGraph 追问** | AI Agent 根据回答质量智能决定追问，模拟真实面试官互动 |
| 📝 **综合诊断报告** | 能力雷达图、优势/劣势分析、岗位差距诊断、训练建议、推荐练习题 |
| 📈 **成长分析** | 面试趋势追踪、能力维度变化、薄弱能力识别 |
| 🎤 **语音转写** | 浏览器录音 + ASR 转写，模拟真实口语作答 |
| 🔊 **TTS 朗读** | 浏览器语音合成，自动朗读题目 |
| 📚 **RAG 知识库** | 上传产品文档/岗位 JD，增强出题与评分的专业性 |
| 📄 **简历增强** | 上传简历，AI 结合简历背景出题，模拟真实面试场景 |
| 🎭 **虚拟面试官** | 本地 SVG/CSS 虚拟面试官 + 可选云端数字人形象 |
| 🔐 **JWT 认证** | 注册/登录/鉴权，保护用户数据 |

---

## 🎯 面试类型

- **技术面试** — 技术原理、工程实现、性能与可靠性
- **项目面试** — 项目背景、职责、协作、落地与复盘
- **综合面试** — 项目、技术、沟通、排错与成长
- **产品面试** — 产品设计、需求分析、用户研究、数据分析、A/B测试、产品策略、PRD撰写、竞品分析、AI产品特性

---

## 🏗️ 技术栈

### 前端
- React 19 + TypeScript 6
- Vite 8
- Ant Design 6
- TanStack Query 5
- Zustand 5
- ECharts 6

### 后端
- Python 3.12+ + FastAPI
- SQLAlchemy Async + MySQL 8
- Alembic 数据库迁移
- LangGraph 1.2 Agent 工作流
- OpenAI 兼容 API（百炼 Qwen）
- DashScope ASR 语音转写

---

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Node.js 20.19+
- MySQL 8

### 1. 克隆项目
```bash
git clone https://github.com/YOUR_USERNAME/mianzhi-ai.git
cd mianzhi-ai
```

### 2. 配置环境变量
```bash
cp .env.example .env
```
编辑 `.env`，填入数据库连接、LLM API Key 等配置：

```env
DATABASE_URL=mysql+asyncmy://ai_interview_user:YOUR_PASSWORD@127.0.0.1:3306/ai_interview
JWT_SECRET_KEY=生成一个长随机字符串
LLM_API_KEY=你的百炼API_KEY
LLM_BASE_URL=https://YOUR_WORKSPACE.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
ASR_API_KEY=你的ASR_API_KEY
EMBEDDING_API_KEY=你的EMBEDDING_API_KEY
```

### 3. 创建数据库
```sql
CREATE DATABASE IF NOT EXISTS ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'ai_interview_user'@'%' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON ai_interview.* TO 'ai_interview_user'@'%';
FLUSH PRIVILEGES;
```

### 4. 后端启动
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 5. 前端启动
```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`，注册账号后即可开始训练。

---

## 📁 项目结构

```
mianzhi-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph Agent 工作流
│   │   ├── api/             # FastAPI 路由
│   │   ├── core/            # 配置、安全、异常处理
│   │   ├── db/              # 数据库会话与基类
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── prompts/         # LLM 提示词（出题/评分/追问/报告）
│   │   ├── schemas/         # Pydantic 数据校验
│   │   ├── services/        # 业务逻辑层
│   │   └── tasks/           # 异步任务
│   ├── alembic/             # 数据库迁移
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/             # API 客户端与类型定义
│   │   ├── components/      # 可复用组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── pages/           # 页面组件
│   │   ├── stores/          # Zustand 状态管理
│   │   └── types/           # TypeScript 类型
│   ├── package.json
│   └── vite.config.ts
├── docs/                    # 文档
├── third_party/             # 第三方 SDK
├── .env.example             # 环境变量模板
└── README.md
```

---

## 🧪 质量检查

```powershell
# 后端
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .

# 前端
cd frontend
npm run build
```

---

## ⚠️ 安全提醒

- **不要**提交 `.env` 文件到 Git
- **不要**将 API Key、密码写入源码或文档
- **不要**在日志中输出敏感信息

---

## 📄 License

MIT

---

## 🤝 贡献

欢迎提交 Issue 和 PR。本项目专注于 AI 产品经理面试训练场景，如有其他岗位场景的需求欢迎讨论。

---

*Built with ❤️ for AI Product Managers*
