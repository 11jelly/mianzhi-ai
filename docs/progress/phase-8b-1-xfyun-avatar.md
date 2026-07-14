# Phase 8B-1: Xfyun Cloud Avatar Trial Display

## Scope

This phase adds an optional frontend-only cloud avatar trial panel to the
interview detail page.

The module is a pluggable presentation layer only. It does not participate in:

- Qwen question generation
- LangGraph follow-up decisions
- RAG retrieval
- browser recording or Bailian ASR
- answer scoring
- report generation
- database writes

No backend API, Alembic migration, database table, or server-side dependency is
added in this phase.

## SDK Source

The official local SDK package is copied from:

```text
third_party/xfyun-avatar/avatar-sdk-web_3.2.3.1002/esm
```

to:

```text
frontend/src/vendor/xfyun-avatar-sdk/esm
```

The source SDK under `third_party` is kept unchanged. The frontend imports the
SDK from:

```text
frontend/src/vendor/xfyun-avatar-sdk/esm/index.js
```

## Environment Template

`frontend/.env.local.example` documents the local Vite variables:

```env
VITE_XFYUN_AVATAR_ENABLED=false
VITE_XFYUN_AVATAR_APP_ID=
VITE_XFYUN_AVATAR_API_KEY=
VITE_XFYUN_AVATAR_API_SECRET=
VITE_XFYUN_AVATAR_ID=110017006
VITE_XFYUN_AVATAR_VCN=x4_mingge
```

Do not commit real credentials. Vite variables are bundled into frontend code,
so this setup is suitable only for a local course demo. After a real demo, reset
or rotate the APISecret/API key in the Xfyun console.

## SDK Call Chain

The implementation uses the current SDK API:

```text
AvatarPlatform
  -> setApiInfo
  -> setGlobalParams
  -> start
  -> writeText
  -> interrupt
  -> stop
  -> destroy
```

It does not use the old `VMS.start()` or `VMS.textDriver()` APIs.

## UI Behavior

The interview detail page now includes an experimental area:

```text
Cloud Avatar (Xfyun Trial)
```

The cloud avatar is initialized only after the user explicitly clicks the enable
button. Text driving is used only for the current question text. Audio driving,
microphone streaming, realtime text streaming, and cloud TTS replacement are not
implemented.

If the feature is disabled, credentials are incomplete, SDK startup fails, or
text driving fails, the page falls back to the Phase 8A local CSS/SVG virtual
interviewer and existing browser SpeechSynthesis button. Interview answering,
recording, scoring, follow-up, report, and RAG flows remain available.

## Lifecycle Fixes

The interview detail page owns one unified playback stop path. It cancels browser
SpeechSynthesis, clears local speaking state, and interrupts the Xfyun avatar
without destroying the SDK instance. Destruction is reserved for explicit close,
page unmount, route leave, initialization failure cleanup, and `COMPLETED`
sessions.

The unified stop path is called before recording, before answer submission,
before switching to the next question, before browser TTS starts, before cloud
avatar text driving starts, on manual interrupt, on explicit cloud avatar close,
on page unmount, and when the session becomes `COMPLETED`.

The Xfyun SDK can emit delayed `frame_start` or `frame_stop` events after an
interrupted utterance. The hook guards these events with a playback generation
flag, an expected-playback flag, and the current question id. A delayed event is
ignored when the page is recording, processing ASR/scoring/report work, already
completed, or no longer on the same question.

`frame_stop` never forces the interviewer back to `IDLE`; it resolves the current
priority instead:

```text
COMPLETED
> THINKING
> LISTENING
> IDLE
```

For `COMPLETED` interview sessions, the cloud avatar panel does not show enable,
read, interrupt, or close controls. If a running interview becomes completed, the
page interrupts playback, stops and destroys the SDK instance, clears the
reference, and leaves the Phase 8A local virtual interviewer in `COMPLETED`.

## Proxy Decision

No Vite proxy is added in this phase. A proxy should only be added after a real
browser test confirms a concrete `/vmss` CORS or networking issue. Keeping the
default network path makes the local trial smaller and easier to reason about.

## Manual Test Steps

1. Copy `frontend/.env.local.example` to `frontend/.env.local` locally.
2. Fill Xfyun trial credentials and set `VITE_XFYUN_AVATAR_ENABLED=true`.
3. Start the frontend with `npm run dev`.
4. Log in and open an interview detail page with a current question.
5. Confirm the Phase 8A local virtual interviewer remains visible.
6. Click "Enable cloud avatar".
7. Confirm the SDK canvas/video area starts without blocking the page.
8. Click "Cloud avatar reads current question".
9. Confirm the avatar speaks or animates from the SDK.
10. Click "Interrupt".
11. Confirm the avatar stops speaking and the local interview controls still work.
12. Disable or remove one Vite credential and restart the frontend.
13. Confirm the cloud avatar button is unavailable and the local avatar/browser TTS
    fallback still works.

## Known Limits

- This is a local course demo integration, not a production public deployment.
- Frontend Vite credentials are visible in browser assets.
- The module is text-driven only and does not perform real lip-sync validation.
- It does not drive or replace the existing browser recording, ASR, scoring, or
  report process.
- Browser/network compatibility must still be verified with real Xfyun trial
  credentials on the target machine.

## Suggested Commit Message

```text
feat(frontend): add optional xfyun cloud avatar trial panel
```
