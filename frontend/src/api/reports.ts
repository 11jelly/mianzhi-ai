import { apiClient } from './client'
import type { InterviewReport } from './types'

export async function generateInterviewReport(sessionId: string): Promise<InterviewReport> {
  const response = await apiClient.post<InterviewReport>(
    `/api/v1/interviews/${sessionId}/report`,
  )
  return response.data
}

export async function getInterviewReport(sessionId: string): Promise<InterviewReport> {
  const response = await apiClient.get<InterviewReport>(
    `/api/v1/interviews/${sessionId}/report`,
  )
  return response.data
}
