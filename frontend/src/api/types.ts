export type User = {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type LoginRequest = {
  username_or_email: string
  password: string
}

export type RegisterRequest = {
  username: string
  email: string
  password: string
}

export type TokenResponse = {
  access_token: string
  token_type: 'bearer'
}

export type Difficulty = 'junior' | 'intermediate' | 'senior'
export type InterviewType = 'technical' | 'project' | 'comprehensive' | 'product'
export type QuestionCount = 3 | 5 | 8

export type InterviewCreateRequest = {
  target_role: string
  difficulty: Difficulty
  interview_type: InterviewType
  question_count: QuestionCount
  knowledge_base_ids?: string[]
  use_active_resume?: boolean
}

export type InterviewKnowledgeBase = {
  id: string
  name: string
  description: string | null
}

export type InterviewSession = {
  id: string
  target_role: string
  difficulty: Difficulty
  interview_type: InterviewType
  question_count: number
  current_question_index: number
  current_question_id: string | null
  follow_up_count: number
  status: 'CREATED' | 'IN_PROGRESS' | 'READY_FOR_REPORT' | 'COMPLETED'
  knowledge_bases?: InterviewKnowledgeBase[]
  use_active_resume?: boolean
  resume?: {
    resume_id: string | null
    resume_title: string
    used_context: boolean
  } | null
  created_at: string
  updated_at: string
}

export type QuestionType = 'PRIMARY' | 'FOLLOW_UP'

export type InterviewQuestion = {
  id: string
  session_id: string
  sequence: number
  category: string
  question_text: string
  question_type: QuestionType
  parent_question_id: string | null
  created_at: string
}

export type Evaluation = {
  id: string
  answer_id: string
  total_score: number
  logic_score: number
  technical_score: number
  expression_score: number
  project_depth_score: number
  strengths: string[]
  weaknesses: string[]
  evidence_items?: AnswerEvidenceItem[]
  expression_metrics?: ExpressionMetrics | null
  improvement_suggestion: string
  detailed_feedback: string
  created_at: string
}

export type EvidenceDimension = 'logic' | 'technical' | 'expression' | 'project_depth'
export type EvidencePolarity = 'strength' | 'improvement'

export type AnswerEvidenceItem = {
  dimension: EvidenceDimension
  polarity: EvidencePolarity
  quote: string
  reason: string
  suggestion: string | null
}

export type ExpressionMetrics = {
  character_count: number
  sentence_count: number
  average_sentence_length: number | null
  filler_word_count: number
  filler_word_rate: number
  repetition_hint: string | null
  structure_signal_count: number
  estimated_speech_rate: number | null
  speech_rate_unit: string | null
  speech_rate_status: string
  speech_rate_note: string
}

export type InterviewAnswer = {
  id: string
  session_id: string
  question_id: string
  answer_text: string
  recording_duration_seconds: number | null
  created_at: string
  updated_at: string
}

export type AnswerSubmitRequest = {
  question_id: string
  answer_text: string
  recording_duration_seconds?: number | null
}

export type AnswerSubmitResponse = {
  answer: InterviewAnswer
  evaluation: Evaluation
  session_status: 'IN_PROGRESS' | 'READY_FOR_REPORT'
  answered_question_count: number
  question_count: number
  next_question: InterviewQuestion | null
  agent_action: 'FOLLOW_UP' | 'NEXT_PRIMARY' | 'READY_FOR_REPORT' | null
  agent_reason_summary: string | null
}

export type AnswerHistoryItem = {
  question_id: string
  sequence: number
  category: string
  question_text: string
  question_type: QuestionType
  parent_question_id: string | null
  answer_text: string
  recording_duration_seconds: number | null
  evaluation: Evaluation
  created_at: string
}

export type AgentEvent = {
  id: string
  session_id: string
  source_question_id: string
  event_type: string
  decision: 'FOLLOW_UP' | 'NEXT_PRIMARY' | 'READY_FOR_REPORT' | string
  reason_summary: string | null
  follow_up_question_id: string | null
  created_at: string
}

export type ImprovementPlanItem = {
  priority: number
  topic: string
  reason: string
  actions: string[]
  expected_outcome: string
}

export type InterviewReport = {
  id: string
  session_id: string
  overall_score: number
  logic_score: number
  technical_score: number
  expression_score: number
  project_depth_score: number
  summary: string
  strengths: string[]
  weaknesses: string[]
  role_gap_analysis: string
  improvement_plan: ImprovementPlanItem[]
  next_practice_questions: string[]
  answer_evidence?: AnswerEvidenceGroup[]
  expression_analysis?: ExpressionAnalysisReport | null
  created_at: string
  updated_at: string
}

export type AnswerEvidenceGroup = {
  question_id: string
  sequence: number
  category: string
  question_text: string
  question_type: QuestionType
  parent_question_id: string | null
  answer_text: string
  evidence_items: AnswerEvidenceItem[]
}

export type ExpressionAnalysisAnswerItem = {
  question_id: string
  sequence: number
  question_text: string
  answer_text: string
  recording_duration_seconds: number | null
  metrics: ExpressionMetrics | null
}

export type ExpressionAnalysisReport = {
  summary: {
    average_answer_length: number | null
    average_sentence_length: number | null
    total_filler_word_count: number | null
    total_structure_signal_count: number | null
    average_estimated_speech_rate: number | null
    speech_rate_unit: string | null
    sample_size: number
    speech_rate_sample_size: number
  }
  answers: ExpressionAnalysisAnswerItem[]
}

export type InterviewStartResponse = {
  session_id: string
  status: 'IN_PROGRESS'
  question_count: number
  current_question_index: number
  current_question: InterviewQuestion
}

export type PageMeta = {
  page: number
  page_size: number
  total: number
}

export type PageResponse<T> = {
  items: T[]
  meta: PageMeta
}

export type HealthResponse = {
  status: string
  service: string
  timestamp: string
}
