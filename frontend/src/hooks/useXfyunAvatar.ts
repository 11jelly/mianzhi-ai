import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { InterviewerState } from '../types/interviewer'
import type { XfyunAvatarConfig, XfyunAvatarStatus } from '../types/xfyunAvatar'
import AvatarPlatform, {
  PlayerEvents,
  SDKEvents,
  type TextDriverExtend,
} from '../vendor/xfyun-avatar-sdk/esm/index.js'

type AvatarInstance = InstanceType<typeof AvatarPlatform>

type AvatarRuntimeState = {
  completed?: boolean
  thinking?: boolean
  listening?: boolean
  currentQuestionId?: string
}

type UseXfyunAvatarOptions = {
  onStateChange?: (state: InterviewerState) => void
  getRuntimeState?: () => AvatarRuntimeState
}

const fallbackMessage = '云端数字人暂不可用，已切换为本地虚拟面试官与浏览器朗读。'

function readConfig(): XfyunAvatarConfig {
  return {
    enabled: import.meta.env.VITE_XFYUN_AVATAR_ENABLED === 'true',
    appId: import.meta.env.VITE_XFYUN_AVATAR_APP_ID ?? '',
    apiKey: import.meta.env.VITE_XFYUN_AVATAR_API_KEY ?? '',
    apiSecret: import.meta.env.VITE_XFYUN_AVATAR_API_SECRET ?? '',
    avatarId: import.meta.env.VITE_XFYUN_AVATAR_ID ?? '110017006',
    vcn: import.meta.env.VITE_XFYUN_AVATAR_VCN ?? 'x4_mingge',
  }
}

function isConfigured(config: XfyunAvatarConfig) {
  return Boolean(
    config.enabled &&
      config.appId &&
      config.apiKey &&
      config.apiSecret &&
      config.avatarId &&
      config.vcn,
  )
}

function writeTextOptions(vcn: string): TextDriverExtend {
  return {
    tts: {
      vcn,
      speed: 50,
      pitch: 50,
      volume: 50,
      audio: {
        sample_rate: 24000,
      },
    },
    avatar_dispatch: {
      interactive_mode: 1 as never,
      enable_action_status: 1,
    },
    air: {
      air: 1,
    },
  }
}

function resolveState(runtime?: AvatarRuntimeState): InterviewerState {
  if (runtime?.completed) {
    return 'COMPLETED'
  }
  if (runtime?.thinking) {
    return 'THINKING'
  }
  if (runtime?.listening) {
    return 'LISTENING'
  }
  return 'IDLE'
}

export function useXfyunAvatar({
  onStateChange,
  getRuntimeState,
}: UseXfyunAvatarOptions = {}) {
  const config = useMemo(readConfig, [])
  const configured = isConfigured(config)
  const [status, setStatus] = useState<XfyunAvatarStatus>(
    config.enabled ? (configured ? 'ready' : 'unconfigured') : 'disabled',
  )
  const [message, setMessage] = useState<string | null>(
    config.enabled && !configured ? '云端数字人配置不完整，请检查前端本地配置。' : null,
  )
  const [desiredEnabled, setDesiredEnabled] = useState(false)
  const [wrapperVersion, setWrapperVersion] = useState(0)
  const instanceRef = useRef<AvatarInstance | null>(null)
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const reconnectingRef = useRef(false)
  const handledWrapperVersionRef = useRef(0)
  const playbackExpectedRef = useRef(false)
  const playbackGenerationRef = useRef(0)
  const playbackQuestionIdRef = useRef<string | undefined>(undefined)

  const invalidatePlayback = useCallback(() => {
    playbackGenerationRef.current += 1
    playbackExpectedRef.current = false
    playbackQuestionIdRef.current = undefined
  }, [])

  const updateToCurrentPriority = useCallback(() => {
    onStateChange?.(resolveState(getRuntimeState?.()))
  }, [getRuntimeState, onStateChange])

  const canAcceptSpeakingEvent = useCallback(() => {
    const runtime = getRuntimeState?.()
    return Boolean(
      playbackExpectedRef.current &&
        !runtime?.completed &&
        !runtime?.listening &&
        !runtime?.thinking &&
        (!runtime?.currentQuestionId ||
          runtime.currentQuestionId === playbackQuestionIdRef.current),
    )
  }, [getRuntimeState])

  const cleanup = useCallback(() => {
    invalidatePlayback()
    const instance = instanceRef.current
    if (!instance) {
      updateToCurrentPriority()
      setStatus(config.enabled ? (configured ? 'ready' : 'unconfigured') : 'disabled')
      return
    }
    try {
      instance.stop()
      instance.destroy()
    } catch {
      // Cleanup must never block the interview flow.
    }
    instanceRef.current = null
    updateToCurrentPriority()
    setStatus(config.enabled ? (configured ? 'ready' : 'unconfigured') : 'disabled')
  }, [config.enabled, configured, invalidatePlayback, updateToCurrentPriority])

  useEffect(() => cleanup, [cleanup])

  const setWrapperRef = useCallback((node: HTMLDivElement | null) => {
    if (wrapperRef.current === node) {
      return
    }
    wrapperRef.current = node
    setWrapperVersion((version) => version + 1)
  }, [])

  const enable = useCallback(async () => {
    setDesiredEnabled(true)
    if (getRuntimeState?.().completed) {
      setMessage('本轮面试已完成，云端数字人已停止。')
      updateToCurrentPriority()
      return false
    }
    if (!configured || !wrapperRef.current) {
      setStatus(config.enabled ? 'unconfigured' : 'disabled')
      setMessage('云端数字人配置不完整或舞台尚未挂载，请使用本地虚拟面试官与浏览器朗读。')
      return false
    }

    cleanup()
    setStatus('starting')
    setMessage(null)

    try {
      const instance = new AvatarPlatform({ useInlinePlayer: true })
      instanceRef.current = instance
      instance
        .on(SDKEvents.stream_start, () => {
          setStatus('running')
          updateToCurrentPriority()
        })
        .on(SDKEvents.frame_start, () => {
          if (!canAcceptSpeakingEvent()) {
            updateToCurrentPriority()
            return
          }
          setStatus('speaking')
          onStateChange?.('SPEAKING')
        })
        .on(SDKEvents.frame_stop, () => {
          setStatus('running')
          updateToCurrentPriority()
        })
        .on(SDKEvents.disconnected, () => {
          setStatus('ready')
          invalidatePlayback()
          updateToCurrentPriority()
        })
        .on(SDKEvents.error, () => {
          setStatus('error')
          setMessage(fallbackMessage)
          invalidatePlayback()
          updateToCurrentPriority()
        })

      instance.setApiInfo({
        appId: config.appId,
        apiKey: config.apiKey,
        apiSecret: config.apiSecret,
      })
      instance.setGlobalParams({
        stream: {
          protocol: 'xrtc',
          fps: 25,
          alpha: 0,
        },
        avatar: {
          avatar_id: config.avatarId,
          width: 1280,
          height: 720,
          audio_format: 2,
        },
        tts: {
          vcn: config.vcn,
          speed: 50,
          pitch: 50,
          volume: 50,
          audio: {
            sample_rate: 24000,
          },
        },
        air: {
          air: 1,
        },
      })
      await instance.start({ wrapper: wrapperRef.current })
      instance.player?.on(PlayerEvents.stop, () => {
        setStatus('running')
        updateToCurrentPriority()
      })
      setStatus('running')
      updateToCurrentPriority()
      return true
    } catch {
      setStatus('error')
      setMessage(fallbackMessage)
      invalidatePlayback()
      try {
        instanceRef.current?.destroy()
      } catch {
        // Ignore destroy failures and keep fallback available.
      }
      instanceRef.current = null
      updateToCurrentPriority()
      return false
    }
  }, [
    canAcceptSpeakingEvent,
    cleanup,
    config,
    configured,
    getRuntimeState,
    invalidatePlayback,
    onStateChange,
    updateToCurrentPriority,
  ])

  useEffect(() => {
    if (wrapperVersion === handledWrapperVersionRef.current) {
      return
    }
    handledWrapperVersionRef.current = wrapperVersion

    if (
      !desiredEnabled ||
      reconnectingRef.current ||
      !wrapperRef.current ||
      getRuntimeState?.().completed ||
      status === 'starting'
    ) {
      return
    }

    if (status === 'running' || status === 'speaking' || status === 'ready' || status === 'error') {
      reconnectingRef.current = true
      void enable().finally(() => {
        reconnectingRef.current = false
      })
    }
  }, [desiredEnabled, enable, getRuntimeState, status, wrapperVersion])

  const speak = useCallback(
    async (text: string, questionId?: string) => {
      const instance = instanceRef.current
      if (!instance) {
        setMessage('请先启用云端数字人；也可以继续使用浏览器朗读。')
        return false
      }
      if (getRuntimeState?.().completed) {
        invalidatePlayback()
        updateToCurrentPriority()
        return false
      }

      const generation = playbackGenerationRef.current + 1
      playbackGenerationRef.current = generation
      playbackExpectedRef.current = true
      playbackQuestionIdRef.current = questionId

      try {
        await instance.interrupt()
        if (playbackGenerationRef.current !== generation) {
          return false
        }
        setStatus('speaking')
        onStateChange?.('SPEAKING')
        await instance.writeText(text, writeTextOptions(config.vcn))
        return true
      } catch {
        invalidatePlayback()
        setStatus('error')
        setMessage(fallbackMessage)
        updateToCurrentPriority()
        return false
      }
    },
    [config.vcn, getRuntimeState, invalidatePlayback, onStateChange, updateToCurrentPriority],
  )

  const interrupt = useCallback(async () => {
    invalidatePlayback()
    try {
      await instanceRef.current?.interrupt()
    } catch {
      setMessage(fallbackMessage)
    } finally {
      if (instanceRef.current) {
        setStatus('running')
      }
      updateToCurrentPriority()
    }
  }, [invalidatePlayback, updateToCurrentPriority])

  const disable = useCallback(() => {
    setDesiredEnabled(false)
    cleanup()
    setMessage('已关闭云端数字人，可继续使用本地虚拟面试官与浏览器朗读。')
  }, [cleanup])

  const destroy = useCallback(async () => {
    setDesiredEnabled(false)
    cleanup()
  }, [cleanup])

  return {
    config,
    configured,
    status,
    message,
    wrapperRef: setWrapperRef,
    enable,
    speak,
    interrupt,
    disable,
    destroy,
    isRunning: Boolean(instanceRef.current),
  }
}

export type XfyunAvatarController = ReturnType<typeof useXfyunAvatar>
