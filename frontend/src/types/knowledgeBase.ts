export type KnowledgeBase = {
  id: string
  name: string
  description: string | null
  document_count: number
  chunk_count: number
  status: string
  created_at: string
  updated_at: string
}

export type KnowledgeBaseCreateRequest = {
  name: string
  description?: string
}

export type KnowledgeDocument = {
  id: string
  knowledge_base_id: string
  original_filename: string
  file_type: string
  content_hash: string
  extracted_text_length: number
  status: string
  error_message: string | null
  chunk_count: number
  created_at: string
  updated_at: string
}

export type KnowledgeSearchItem = {
  chunk_id: string
  document_name: string
  content_preview: string
  score: number
}

export type KnowledgeSearchResponse = {
  items: KnowledgeSearchItem[]
}
