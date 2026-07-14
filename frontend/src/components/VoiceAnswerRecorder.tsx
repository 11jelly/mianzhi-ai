import {
  AudioOutlined,
  DeleteOutlined,
  LoadingOutlined,
  RedoOutlined,
  StopOutlined,
} from '@ant-design/icons'
import { Alert, Button, Space, Typography } from 'antd'
import { useState } from 'react'

import { getApiErrorMessage } from '../api/client'
import { transcribeSpeech } from '../api/speech'
import { useWavRecorder } from '../hooks/useWavRecorder'

const { Text } = Typography

type VoiceAnswerRecorderProps = {
  disabled?: boolean
  onTranscription: (text: string, durationSeconds: number | null) => void
  onRecordingChange?: (recording: boolean) => void
  onTranscribingChange?: (transcribing: boolean) => void
  beforeStartRecording?: () => Promise<void> | void
}

export function VoiceAnswerRecorder({
  disabled,
  onTranscription,
  onRecordingChange,
  onTranscribingChange,
  beforeStartRecording,
}: VoiceAnswerRecorderProps) {
  const recorder = useWavRecorder()
  const [transcribing, setTranscribing] = useState(false)
  const [transcriptionError, setTranscriptionError] = useState<string | null>(null)

  function updateTranscribing(nextTranscribing: boolean) {
    setTranscribing(nextTranscribing)
    onTranscribingChange?.(nextTranscribing)
  }

  async function startRecording() {
    await beforeStartRecording?.()
    const started = await recorder.startRecording()
    onRecordingChange?.(started)
  }

  async function stopAndTranscribe() {
    const blob = recorder.stopRecording()
    onRecordingChange?.(false)
    if (!blob) {
      return
    }
    updateTranscribing(true)
    setTranscriptionError(null)
    try {
      const result = await transcribeSpeech(blob, recorder.elapsedSeconds || 1)
      onTranscription(result.text, result.duration_seconds ?? recorder.elapsedSeconds ?? null)
    } catch (error) {
      setTranscriptionError(getApiErrorMessage(error))
    } finally {
      updateTranscribing(false)
    }
  }

  function resetRecording() {
    recorder.resetRecording()
    onRecordingChange?.(false)
    updateTranscribing(false)
  }

  return (
    <Space direction="vertical" size={10} className="question-panel">
      <div className="recorder-control-grid">
        <div className="recorder-button-row">
          <Button
            icon={<AudioOutlined />}
            disabled={disabled || recorder.isRecording || transcribing}
            onClick={() => {
              void startRecording()
            }}
          >
            开始录音
          </Button>
          <Button
            danger
            icon={transcribing ? <LoadingOutlined /> : <StopOutlined />}
            disabled={disabled || !recorder.isRecording || transcribing}
            loading={transcribing}
            onClick={() => {
              void stopAndTranscribe()
            }}
          >
            停止并转写
          </Button>
          <Button
            icon={<RedoOutlined />}
            disabled={disabled || recorder.isRecording || transcribing}
            onClick={resetRecording}
          >
            重新录音
          </Button>
        </div>
        <div className="recorder-meta-row">
          <Button
            icon={<DeleteOutlined />}
            disabled={disabled || recorder.isRecording || transcribing || !recorder.audioBlob}
            onClick={resetRecording}
          >
            删除录音
          </Button>
          <Text type={recorder.isRecording ? 'danger' : 'secondary'}>
            录音计时 {formatSeconds(recorder.elapsedSeconds)}
          </Text>
        </div>
      </div>
      {recorder.error && <Alert showIcon type="error" message={recorder.error} />}
      {transcribing && <Alert showIcon type="info" message="正在转写，请稍候。" />}
      {transcriptionError && (
        <Alert
          showIcon
          type="error"
          message={transcriptionError}
          description="已保留当前文本回答，你可以重新录音或继续手动输入。"
        />
      )}
    </Space>
  )
}

function formatSeconds(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(safeSeconds / 60)
  const rest = safeSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
}
