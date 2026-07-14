import type { PageResponse } from '../api/types'

export type AnalyticsReportPoint = {
  session_id: string
  target_role: string
  created_at: string
  overall_score: number
  logic_score: number
  technical_score: number
  expression_score: number
  project_depth_score: number
}

export type AbilityAverages = {
  logic_score: number
  technical_score: number
  expression_score: number
  project_depth_score: number
}

export type WeakestDimension = {
  key: keyof AbilityAverages
  label: string
  average_score: number
  max_score: number
}

export type AnalyticsImprovementPlanItem = {
  priority: string
  topic: string
}

export type AnalyticsOverview = {
  completed_interview_count: number
  average_overall_score: number
  latest_report: AnalyticsReportPoint | null
  ability_averages: AbilityAverages | null
  weakest_dimension: WeakestDimension | null
  latest_improvement_plan: AnalyticsImprovementPlanItem[]
}

export type AnalyticsTrendItem = {
  session_id: string
  target_role: string
  report_created_at: string
  overall_score: number
  logic_score: number
  technical_score: number
  expression_score: number
  project_depth_score: number
}

export type AnalyticsTrendResponse = {
  items: AnalyticsTrendItem[]
}

export type AnalyticsHistoryItem = AnalyticsTrendItem & {
  difficulty: string
  interview_type: string
  knowledge_base_names: string[]
}

export type AnalyticsHistoryResponse = PageResponse<AnalyticsHistoryItem>
