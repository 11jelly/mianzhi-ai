import { apiClient } from './client'
import type { Resume, ResumePasteRequest, ResumeUpdateRequest } from '../types/resume'

export async function listResumes(): Promise<Resume[]> {
  const response = await apiClient.get<Resume[]>('/api/v1/resumes')
  return response.data
}

export async function getResume(resumeId: string): Promise<Resume> {
  const response = await apiClient.get<Resume>(`/api/v1/resumes/${resumeId}`)
  return response.data
}

export async function pasteResume(payload: ResumePasteRequest): Promise<Resume> {
  const response = await apiClient.post<Resume>('/api/v1/resumes/paste', payload)
  return response.data
}

export async function uploadResume(
  file: File,
  title: string,
  activate = true,
): Promise<Resume> {
  const formData = new FormData()
  formData.append('file', file)
  if (title.trim()) {
    formData.append('title', title.trim())
  }
  formData.append('activate', String(activate))
  const response = await apiClient.post<Resume>('/api/v1/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function updateResume(
  resumeId: string,
  payload: ResumeUpdateRequest,
): Promise<Resume> {
  const response = await apiClient.patch<Resume>(`/api/v1/resumes/${resumeId}`, payload)
  return response.data
}

export async function activateResume(resumeId: string): Promise<Resume> {
  const response = await apiClient.post<Resume>(`/api/v1/resumes/${resumeId}/activate`)
  return response.data
}

export async function deactivateResume(resumeId: string): Promise<Resume> {
  const response = await apiClient.post<Resume>(`/api/v1/resumes/${resumeId}/deactivate`)
  return response.data
}

export async function deleteResume(resumeId: string): Promise<void> {
  await apiClient.delete(`/api/v1/resumes/${resumeId}`)
}
