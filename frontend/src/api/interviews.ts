import { apiClient } from './client'
import type {
  AgentEvent,
  AnswerHistoryItem,
  AnswerSubmitRequest,
  AnswerSubmitResponse,
  InterviewCreateRequest,
  InterviewQuestion,
  InterviewSession,
  InterviewStartResponse,
  PageResponse,
} from './types'

export async function createInterview(payload: InterviewCreateRequest): Promise<InterviewSession> {
  const response = await apiClient.post<InterviewSession>('/api/v1/interviews', payload)
  return response.data
}

export async function listInterviews(page = 1, pageSize = 10): Promise<PageResponse<InterviewSession>> {
  const response = await apiClient.get<PageResponse<InterviewSession>>('/api/v1/interviews', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export async function getInterview(sessionId: string): Promise<InterviewSession> {
  const response = await apiClient.get<InterviewSession>(`/api/v1/interviews/${sessionId}`)
  return response.data
}

export async function startInterview(sessionId: string): Promise<InterviewStartResponse> {
  const response = await apiClient.post<InterviewStartResponse>(
    `/api/v1/interviews/${sessionId}/start`,
  )
  return response.data
}

export async function getCurrentQuestion(sessionId: string): Promise<InterviewQuestion> {
  const response = await apiClient.get<InterviewQuestion>(
    `/api/v1/interviews/${sessionId}/current-question`,
  )
  return response.data
}

export async function getInterviewQuestions(sessionId: string): Promise<InterviewQuestion[]> {
  const response = await apiClient.get<InterviewQuestion[]>(
    `/api/v1/interviews/${sessionId}/questions`,
  )
  return response.data
}

export async function submitInterviewAnswer(
  sessionId: string,
  payload: AnswerSubmitRequest,
): Promise<AnswerSubmitResponse> {
  const response = await apiClient.post<AnswerSubmitResponse>(
    `/api/v1/interviews/${sessionId}/answers`,
    payload,
  )
  return response.data
}

export async function getInterviewAnswers(sessionId: string): Promise<AnswerHistoryItem[]> {
  const response = await apiClient.get<AnswerHistoryItem[]>(
    `/api/v1/interviews/${sessionId}/answers`,
  )
  return response.data
}

export async function getInterviewAgentEvents(sessionId: string): Promise<AgentEvent[]> {
  const response = await apiClient.get<AgentEvent[]>(
    `/api/v1/interviews/${sessionId}/agent-events`,
  )
  return response.data
}
