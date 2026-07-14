import { useCallback, useEffect, useRef, useState } from 'react'

const TARGET_SAMPLE_RATE = 16000
const MAX_RECORDING_SECONDS = 300

type RecorderState = 'idle' | 'recording' | 'recorded'

type RecorderSession = {
  audioContext: AudioContext
  mediaStream: MediaStream
  source: MediaStreamAudioSourceNode
  processor: ScriptProcessorNode
  chunks: Float32Array[]
  sourceSampleRate: number
}

export function useWavRecorder(maxSeconds = MAX_RECORDING_SECONDS) {
  const [state, setState] = useState<RecorderState>('idle')
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const sessionRef = useRef<RecorderSession | null>(null)
  const timerRef = useRef<number | null>(null)
  const startedAtRef = useRef<number>(0)

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const cleanupSession = useCallback(() => {
    const session = sessionRef.current
    if (!session) {
      return
    }
    session.processor.disconnect()
    session.source.disconnect()
    session.mediaStream.getTracks().forEach((track) => track.stop())
    void session.audioContext.close()
    sessionRef.current = null
  }, [])

  const stopRecording = useCallback(() => {
    const session = sessionRef.current
    if (!session) {
      return null
    }
    clearTimer()
    const duration = Math.min(
      maxSeconds,
      Math.max(0, (Date.now() - startedAtRef.current) / 1000),
    )
    const samples = mergeChunks(session.chunks)
    const resampled = resampleLinear(samples, session.sourceSampleRate, TARGET_SAMPLE_RATE)
    const wavBlob = encodeWav(resampled, TARGET_SAMPLE_RATE)
    cleanupSession()
    setAudioBlob(wavBlob)
    setElapsedSeconds(duration)
    setState('recorded')
    return wavBlob
  }, [cleanupSession, clearTimer, maxSeconds])

  const startRecording = useCallback(async () => {
    if (state === 'recording') {
      return true
    }
    setError(null)
    setAudioBlob(null)
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const AudioContextClass =
        window.AudioContext ||
        (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!AudioContextClass) {
        throw new Error('AudioContext is not supported.')
      }
      const audioContext = new AudioContextClass()
      const source = audioContext.createMediaStreamSource(mediaStream)
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      const chunks: Float32Array[] = []

      processor.onaudioprocess = (event) => {
        chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)))
      }
      source.connect(processor)
      processor.connect(audioContext.destination)

      sessionRef.current = {
        audioContext,
        mediaStream,
        source,
        processor,
        chunks,
        sourceSampleRate: audioContext.sampleRate,
      }
      startedAtRef.current = Date.now()
      setElapsedSeconds(0)
      setState('recording')
      timerRef.current = window.setInterval(() => {
        const elapsed = Math.floor((Date.now() - startedAtRef.current) / 1000)
        setElapsedSeconds(Math.min(elapsed, maxSeconds))
        if (elapsed >= maxSeconds) {
          stopRecording()
        }
      }, 500)
      return true
    } catch {
      setError('无法访问麦克风，请检查浏览器权限后重试。')
      setState('idle')
      return false
    }
  }, [maxSeconds, state, stopRecording])

  const resetRecording = useCallback(() => {
    clearTimer()
    cleanupSession()
    setAudioBlob(null)
    setElapsedSeconds(0)
    setError(null)
    setState('idle')
  }, [cleanupSession, clearTimer])

  useEffect(() => {
    return () => {
      clearTimer()
      cleanupSession()
    }
  }, [cleanupSession, clearTimer])

  return {
    state,
    isRecording: state === 'recording',
    audioBlob,
    elapsedSeconds,
    error,
    startRecording,
    stopRecording,
    resetRecording,
  }
}

function mergeChunks(chunks: Float32Array[]) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const merged = new Float32Array(totalLength)
  let offset = 0
  chunks.forEach((chunk) => {
    merged.set(chunk, offset)
    offset += chunk.length
  })
  return merged
}

function resampleLinear(samples: Float32Array, sourceRate: number, targetRate: number) {
  if (sourceRate === targetRate) {
    return samples
  }
  const targetLength = Math.round((samples.length * targetRate) / sourceRate)
  const result = new Float32Array(targetLength)
  const ratio = (samples.length - 1) / Math.max(targetLength - 1, 1)
  for (let index = 0; index < targetLength; index += 1) {
    const sourceIndex = index * ratio
    const left = Math.floor(sourceIndex)
    const right = Math.min(left + 1, samples.length - 1)
    const fraction = sourceIndex - left
    result[index] = samples[left] * (1 - fraction) + samples[right] * fraction
  }
  return result
}

function encodeWav(samples: Float32Array, sampleRate: number) {
  const bytesPerSample = 2
  const dataLength = samples.length * bytesPerSample
  const buffer = new ArrayBuffer(44 + dataLength)
  const view = new DataView(buffer)
  writeAscii(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataLength, true)
  writeAscii(view, 8, 'WAVE')
  writeAscii(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * bytesPerSample, true)
  view.setUint16(32, bytesPerSample, true)
  view.setUint16(34, 16, true)
  writeAscii(view, 36, 'data')
  view.setUint32(40, dataLength, true)

  let offset = 44
  samples.forEach((sample) => {
    const clipped = Math.max(-1, Math.min(1, sample))
    view.setInt16(offset, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true)
    offset += 2
  })
  return new Blob([view], { type: 'audio/wav' })
}

function writeAscii(view: DataView, offset: number, value: string) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index))
  }
}
