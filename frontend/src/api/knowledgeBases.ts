import type {
  KnowledgeBase,
  KnowledgeBaseCreateRequest,
  KnowledgeDocument,
  KnowledgeSearchResponse,
} from '../types/knowledgeBase'
import { apiClient } from './client'

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const response = await apiClient.get<KnowledgeBase[]>('/api/v1/knowledge-bases')
  return response.data
}

export async function createKnowledgeBase(
  payload: KnowledgeBaseCreateRequest,
): Promise<KnowledgeBase> {
  const response = await apiClient.post<KnowledgeBase>('/api/v1/knowledge-bases', payload)
  return response.data
}

export async function getKnowledgeBase(knowledgeBaseId: string): Promise<KnowledgeBase> {
  const response = await apiClient.get<KnowledgeBase>(`/api/v1/knowledge-bases/${knowledgeBaseId}`)
  return response.data
}

export async function deleteKnowledgeBase(knowledgeBaseId: string): Promise<void> {
  await apiClient.delete(`/api/v1/knowledge-bases/${knowledgeBaseId}`)
}

export async function listKnowledgeDocuments(
  knowledgeBaseId: string,
): Promise<KnowledgeDocument[]> {
  const response = await apiClient.get<KnowledgeDocument[]>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents`,
  )
  return response.data
}

export async function uploadKnowledgeDocument(
  knowledgeBaseId: string,
  file: File,
): Promise<KnowledgeDocument> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<KnowledgeDocument>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return response.data
}

export async function deleteKnowledgeDocument(
  knowledgeBaseId: string,
  documentId: string,
): Promise<void> {
  await apiClient.delete(`/api/v1/knowledge-bases/${knowledgeBaseId}/documents/${documentId}`)
}

export async function searchKnowledgeBase(
  knowledgeBaseId: string,
  query: string,
): Promise<KnowledgeSearchResponse> {
  const response = await apiClient.post<KnowledgeSearchResponse>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/search`,
    { query },
  )
  return response.data
}
