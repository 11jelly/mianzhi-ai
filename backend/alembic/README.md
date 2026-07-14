# Alembic 使用说明

当前阶段只初始化迁移目录，不创建业务模型、不生成 migration、不执行 upgrade。

后续生成迁移前，请先在 `backend` 目录配置真实的 `DATABASE_URL` 环境变量或 `.env` 文件：

```powershell
DATABASE_URL=mysql+asyncmy://ai_interview_user:YOUR_PASSWORD@127.0.0.1:3306/ai_interview
```

生成迁移：

```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe change"
```

执行迁移：

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

回滚一个版本：

```powershell
.\.venv\Scripts\alembic.exe downgrade -1
```
