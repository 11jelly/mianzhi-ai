export type ResumeStatus = 'PROCESSING' | 'READY' | 'FAILED'
export type ResumeSourceType = 'UPLOAD' | 'PASTE'

export type Resume = {
  id: string
  title: string
  source_type: ResumeSourceType
  original_filename: string | null
  normalized_text: string | null
  content_hash: string
  status: ResumeStatus
  error_message: string | null
  is_active: boolean
  extracted_text_length: number
  chunk_count: number
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export type ResumePasteRequest = {
  title: string
  resume_text: string
  activate?: boolean
}

export type ResumeUpdateRequest = {
  title?: string
}
