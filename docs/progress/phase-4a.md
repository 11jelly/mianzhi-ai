# 阶段 4A 进度记录

日期：2026-06-22

## 功能范围

- 浏览器原生 TTS 朗读当前题目和 AI 追问。
- 浏览器麦克风录音。
- 前端将录音编码为 WAV。
- 后端上传 WAV 到百炼 DashScope ASR Provider 转写。
- 转写文本自动填入现有回答框。
- 用户可编辑确认后继续使用原有“提交并获取 AI 评分”流程。

本阶段不包含：
- 实时 WebSocket ASR。
- 云端 TTS。
- 本地 Whisper、本地模型、FFmpeg。
- RAG、虚拟人、历史趋势分析。

## 语音数据流

```text
题目显示
  -> 用户点击朗读题目
  -> 浏览器 SpeechSynthesis 朗读
  -> 用户点击开始录音
  -> getUserMedia + Web Audio API 采集 PCM
  -> 停止录音后编码 WAV
  -> POST /api/v1/speech/transcriptions
  -> FastAPI 写入系统临时目录
  -> DashScope ASR Provider 调用百炼 qwen3-asr-flash
  -> 删除临时文件
  -> 返回转写文本
  -> 前端填入 textarea
  -> 用户编辑并手动提交评分
```

## ASR Provider 架构

- `AsrClient` 协议定义 `transcribe_wav(file_path: Path)`。
- `DashScopeAsrClient` 实现百炼云端 ASR。
- DashScope SDK 是正式运行依赖，版本约束为 `dashscope>=1.25.23,<2.0.0`。
- `python-multipart` 是语音上传接口的正式运行依赖，用于解析 `multipart/form-data`。
- `asr_service` 负责上传校验、临时文件写入、清理和错误转换。
- `speech.py` 路由只处理鉴权和请求绑定，不直接调用云厂商 SDK。
- 自动化测试使用 Fake ASR Client，不调用真实百炼 API。

## WAV 录音格式

前端录音格式：
- 采样率：16kHz。
- 声道：单声道。
- 位深：16-bit PCM。
- 容器：WAV。

实现位置：
- `frontend/src/hooks/useWavRecorder.ts`

## 接口说明

```text
POST /api/v1/speech/transcriptions
```

请求：
- JWT 鉴权。
- `multipart/form-data`。
- 文件字段：`audio`。
- 可选字段：`duration_seconds`。

响应：

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

## 数据隐私策略

- 原始音频不写入 MySQL。
- 不新增音频永久存储表。
- 后端只将上传 WAV 写入系统临时目录。
- 无论转写成功或失败，都会在 finally 中删除临时 WAV 文件。
- ASR 接口不创建 `interview_answers`。
- ASR 接口不创建 `answer_evaluations`。
- ASR 接口不修改 `interview_sessions`。

## 修改文件

后端：
- `backend/app/core/config.py`
- `backend/app/schemas/speech.py`
- `backend/app/services/asr_client.py`
- `backend/app/services/asr_service.py`
- `backend/app/api/v1/speech.py`
- `backend/app/api/v1/router.py`
- `backend/pyproject.toml`
- `backend/requirements.txt`
- `backend/tests/test_phase4a_speech.py`

前端：
- `frontend/src/types/speech.ts`
- `frontend/src/api/speech.ts`
- `frontend/src/hooks/useWavRecorder.ts`
- `frontend/src/components/VoiceAnswerRecorder.tsx`
- `frontend/src/components/SpeechSynthesisButton.tsx`
- `frontend/src/pages/InterviewDetailPage.tsx`

文档：
- `README.md`
- `docs/architecture.md`
- `docs/api-design.md`
- `docs/prompt-design.md`
- `docs/progress/phase-4a.md`

## 自动化测试命令

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

## 手工测试步骤

1. 确认根目录 `.env` 已配置 `ASR_API_KEY`，但不要提交或输出真实值。
2. 启动后端。
3. 启动前端。
4. 登录并进入一个 `IN_PROGRESS` 面试会话。
5. 点击“朗读题目”，浏览器应朗读当前题。
6. 再次点击按钮，应停止朗读。
7. 点击“开始录音”，首次使用时浏览器会请求麦克风权限，必须选择允许。
8. 如果浏览器或系统有多个输入设备，确认选择的是正在使用的麦克风。
9. 说出一段回答后点击“停止并转写”。
10. 页面显示“正在转写”，完成后文本自动填入回答框。
11. 编辑文本后点击“提交并获取 AI 评分”。
12. 如果后端生成 AI 追问，追问题旁也可以点击“朗读追问”。

## 已知限制

- 本阶段不是实时 ASR，必须停止录音后上传转写。
- 浏览器 TTS 语音质量取决于用户系统和浏览器可用语音。
- 浏览器拒绝麦克风权限时，只能手动输入或重新授权后再录音。
- 浏览器选择了错误输入设备时，可能录到静音或环境噪声，需要在浏览器/系统设置中切换麦克风。
- 前端未新增大型测试框架，使用 TypeScript build 做静态回归。
- 后端环境需要安装 `dashscope>=1.25.23,<2.0.0` 后才能真实调用百炼 ASR。

## 下一阶段建议

阶段 4B 可以考虑实时转写或语音交互状态优化；RAG 和虚拟人仍建议作为后续独立阶段。

## 建议 Git commit message

```text
feat: add browser voice answer transcription
```
