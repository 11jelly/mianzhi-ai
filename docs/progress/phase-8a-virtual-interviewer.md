# Phase 8A: Virtual Interviewer Display Layer

## Scope

Phase 8A adds a pluggable visual-only "AI Virtual Interviewer" panel to the
interview detail page. It is not a digital-human engine and does not drive any
business workflow.

## What It Does Not Do

- Does not call cloud virtual-human APIs.
- Does not deploy SadTalker or local models.
- Does not call LLM, ASR, Embedding, or external services.
- Does not add backend routes, database tables, Alembic migrations, or `.env`
  configuration.
- Does not store user video, webcam frames, avatars, or biometric data.
- Does not participate in LangGraph follow-up decisions, scoring, RAG retrieval,
  or report generation.

## Visual Design

- Uses a local SVG: `frontend/src/assets/ai-interviewer.svg`.
- Uses CSS animations for calm visual states.
- Does not use real-person photos or remote images.
- Supports `prefers-reduced-motion` by disabling loop animations.

## State Machine

Priority:

```text
COMPLETED > THINKING > LISTENING > SPEAKING > IDLE
```

States:

- `IDLE`: AI interviewer is ready.
- `SPEAKING`: browser SpeechSynthesis is reading the current question.
- `LISTENING`: browser microphone recording is active.
- `THINKING`: ASR transcription, answer scoring, current-question loading,
  report loading, or report generation is in progress.
- `COMPLETED`: the interview session status is `COMPLETED`.

## Relationship To Existing Flow

- TTS remains controlled by `SpeechSynthesisButton`.
- Recording and transcription remain controlled by `VoiceAnswerRecorder`.
- Scoring and follow-up decisions remain controlled by existing answer mutation
  and backend Agent logic.
- Report generation remains unchanged.
- The virtual interviewer only subscribes to status callbacks and mutation/query
  pending states.

## Manual Test Steps

1. Open an interview detail page before starting: the panel should show IDLE.
2. Start an interview and click "朗读题目": the panel should show SPEAKING.
3. Stop speech or wait for speech end: it should return to IDLE.
4. Click "开始录音": the panel should show LISTENING.
5. Click "停止并转写": it should switch to THINKING while ASR is pending.
6. Delete or reset a recording: it should not remain LISTENING.
7. Submit an answer: it should show THINKING while scoring and Agent follow-up
   decisions are pending.
8. Generate the final report: it should show THINKING while the report request
   is pending.
9. After the session becomes `COMPLETED`, it should show COMPLETED.
10. Switch question, leave the page, or refresh: SPEAKING and LISTENING should
    not remain stuck.
11. Enable OS/browser reduced-motion preference and confirm status text remains
    visible while loop animations stop.

## Known Limits

- No real lip sync.
- No digital-human rendering.
- No webcam or face tracking.
- SadTalker is intentionally not deployed in this local course project; it is
  only a distant research option and not recommended for the current setup.

## Next Phase Suggestions

- Phase 8B may optionally explore a cloud virtual-human API behind a strict
  provider abstraction.
- Add lightweight frontend component tests if a test framework is introduced.

## Suggested Git Commit Message

```text
feat: add virtual interviewer display layer
```
