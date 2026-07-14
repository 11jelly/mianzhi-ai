import axios from 'axios'

import { clearStoredToken, getStoredToken } from '../stores/auth'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredToken()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join('; ')
    }
    if (typeof detail === 'string') {
      if (detail.includes('评分 JSON')) {
        return 'AI 暂时无法完成本题评分，请稍后重试。当前回答未保存。'
      }
      return detail
    }
    return error.message
  }
  return '请求失败，请稍后重试。'
}
