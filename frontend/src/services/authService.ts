import { apiGet, apiPost } from '@/lib/apiClient'
import type { Usuario } from '@/types'

export interface TokenResponse {
  access_token: string
  token_type: string
  user: Usuario
}

export const authService = {
  login: (email: string, password: string) => apiPost<TokenResponse>('/auth/login', { email, password }),
  register: (data: { email: string; password: string; nombres: string; apellidos: string }) =>
    apiPost<Usuario>('/auth/register', data),
  me: () => apiGet<Usuario>('/auth/me'),
}
