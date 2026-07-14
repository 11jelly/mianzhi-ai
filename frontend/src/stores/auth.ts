import { create } from 'zustand'

const TOKEN_KEY = 'ai_interview_access_token'

type AuthState = {
  token: string | null
  setToken: (token: string) => void
  clearToken: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(TOKEN_KEY),
  setToken: (token) => {
    localStorage.setItem(TOKEN_KEY, token)
    set({ token })
  },
  clearToken: () => {
    localStorage.removeItem(TOKEN_KEY)
    set({ token: null })
  },
}))

export const getStoredToken = () => localStorage.getItem(TOKEN_KEY)

export const clearStoredToken = () => {
  localStorage.removeItem(TOKEN_KEY)
  useAuthStore.setState({ token: null })
}
