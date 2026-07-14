# Windows 本地环境搭建

## 开发方式

本项目按 Windows 本地开发方式初始化，不使用 WSL、Docker、Redis、Celery、本地 Whisper 或本地大模型。

## 已验证软件版本

- Python 3.12.4
- Node.js 24.17.0
- npm 11.13.0
- MySQL 8.0.26
- Git 2.42.0

## 前端依赖安装与启动

```powershell
cd frontend
npm install
npm run dev
```

构建检查：

```powershell
cd frontend
npm run build
```

## 后端虚拟环境

创建虚拟环境：

```powershell
cd backend
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 拦截脚本：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动后端：

```powershell
uvicorn app.main:app --reload --port 8000
```

## MySQL 连接字符串

格式：

```env
DATABASE_URL=mysql+asyncmy://USER:PASSWORD@HOST:PORT/DATABASE
```

本项目示例：

```env
DATABASE_URL=mysql+asyncmy://ai_interview_user:CHANGE_ME@127.0.0.1:3306/ai_interview
```

当前阶段不连接真实数据库。

## 常用环境检查命令

```powershell
python --version
node --version
npm --version
git --version
mysql --version
```

后端检查：

```powershell
cd backend
ruff check .
pytest
```

健康检查：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

## 常见问题

端口占用：

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

PowerShell 激活虚拟环境失败：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

MySQL 连接失败：

- 确认 MySQL 服务已启动。
- 确认 `DATABASE_URL` 中的主机、端口、用户名、密码和数据库名正确。
- 确认用户具备访问 `ai_interview` 数据库的权限。
