import { apiGet, apiPatch, apiPost, apiPut } from '@/lib/apiClient'
import type { Departamento } from '@/types'

export interface DepartamentoPayload {
  nombre: string
  descripcion?: string | null
}

export const departamentosService = {
  list: () => apiGet<Departamento[]>('/departamentos'),
  create: (data: DepartamentoPayload) => apiPost<Departamento>('/departamentos', data),
  update: (id: number, data: DepartamentoPayload) => apiPut<Departamento>(`/departamentos/${id}`, data),
  /** Desactiva o reactiva. Al desactivar, sus cargos pasan a «Sin asignar». */
  toggleActivo: (id: number) => apiPatch<Departamento>(`/departamentos/${id}/toggle-activo`),
}
