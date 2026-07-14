import { SoundOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useCallback, useEffect, useState } from 'react'

type SpeechSynthesisButtonProps = {
  text: string
  label?: string
  onSpeakingChange?: (speaking: boolean) => void
  beforeSpeak?: () => Promise<void> | void
}

export function SpeechSynthesisButton({
  text,
  label = '朗读题目',
  onSpeakingChange,
  beforeSpeak,
}: SpeechSynthesisButtonProps) {
  const [speaking, setSpeaking] = useState(false)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

  const updateSpeaking = useCallback(
    (nextSpeaking: boolean) => {
      setSpeaking(nextSpeaking)
      onSpeakingChange?.(nextSpeaking)
    },
    [onSpeakingChange],
  )

  useEffect(() => {
    return () => {
      if (supported) {
        window.speechSynthesis.cancel()
        updateSpeaking(false)
      }
    }
  }, [supported, text, updateSpeaking])

  if (!supported) {
    return null
  }

  async function toggleSpeech() {
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel()
      updateSpeaking(false)
      return
    }

    await beforeSpeak?.()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    const voices = window.speechSynthesis.getVoices()
    const chineseVoice = voices.find((voice) => voice.lang.toLowerCase().startsWith('zh'))
    if (chineseVoice) {
      utterance.voice = chineseVoice
    }
    utterance.onend = () => updateSpeaking(false)
    utterance.onerror = () => updateSpeaking(false)
    updateSpeaking(true)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <Button
      icon={<SoundOutlined />}
      onClick={() => {
        void toggleSpeech()
      }}
    >
      {speaking ? '停止朗读' : label}
    </Button>
  )
}
