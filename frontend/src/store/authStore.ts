import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Usuario } from '@/types'
import { authService } from '@/services/authService'
import { ApiError } from '@/lib/apiClient'

interface AuthState {
  user: Usuario | null
  token: string | null
  login: (email: string, password: string) => Promise<{ ok: true } | { ok: false; message: string }>
  register: (data: {
    email: string
    password: string
    nombres: string
    apellidos: string
  }) => Promise<{ ok: true } | { ok: false; message: string }>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: async (email, password) => {
        try {
          const { access_token, user } = await authService.login(email, password)
          set({ token: access_token, user })
          return { ok: true }
        } catch (err) {
          const message = err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor'
          return { ok: false, message }
        }
      },
      register: async (data) => {
        try {
          await authService.register(data)
          return { ok: true }
        } catch (err) {
          const message = err instanceof ApiError ? err.message : 'No se pudo conectar con el servidor'
          return { ok: false, message }
        }
      },
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'ats-auth' }
  )
)

window.addEventListener('ats:unauthorized', () => {
  useAuthStore.getState().logout()
})
