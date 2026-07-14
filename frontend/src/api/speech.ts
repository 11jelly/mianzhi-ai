import { apiClient } from './client'
import type { AsrTranscriptionResult } from '../types/speech'

export async function transcribeSpeech(
  audio: Blob,
  durationSeconds: number,
): Promise<AsrTranscriptionResult> {
  const formData = new FormData()
  formData.append('audio', audio, 'answer.wav')
  formData.append('duration_seconds', String(durationSeconds))

  const response = await apiClient.post<AsrTranscriptionResult>(
    '/api/v1/speech/transcriptions',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  return response.data
}
