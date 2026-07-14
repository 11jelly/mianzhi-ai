import type {
  AnalyticsHistoryResponse,
  AnalyticsOverview,
  AnalyticsTrendResponse,
} from '../types/analytics'
import { apiClient } from './client'

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const response = await apiClient.get<AnalyticsOverview>('/api/v1/analytics/overview')
  return response.data
}

export async function getAnalyticsTrend(
  days = 90,
  targetRole?: string,
): Promise<AnalyticsTrendResponse> {
  const response = await apiClient.get<AnalyticsTrendResponse>('/api/v1/analytics/trend', {
    params: { days, target_role: targetRole || undefined },
  })
  return response.data
}

export async function getAnalyticsHistory(
  page = 1,
  pageSize = 10,
  targetRole?: string,
): Promise<AnalyticsHistoryResponse> {
  const response = await apiClient.get<AnalyticsHistoryResponse>('/api/v1/analytics/history', {
    params: { page, page_size: pageSize, target_role: targetRole || undefined },
  })
  return response.data
}
