import { apiGet, apiPatch, apiPut } from '@/lib/apiClient'
import type { RolNombre, Usuario } from '@/types'

export const usuariosService = {
  list: () => apiGet<Usuario[]>('/users'),
  setRol: (id: string, rol: RolNombre) => apiPut<Usuario>(`/users/${id}/role`, { rol }),
  setActivo: (id: string, activo: boolean) => apiPatch<Usuario>(`/users/${id}/activo`, { activo }),
}
