import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/apiClient'
import type { CatalogoItem, CatalogoTipo } from '@/types'

export const catalogosService = {
  list: (tipo: CatalogoTipo) => apiGet<CatalogoItem[]>(`/catalogos/${tipo}`),
  create: (tipo: CatalogoTipo, nombre: string) => apiPost<CatalogoItem>(`/catalogos/${tipo}`, { nombre }),
  update: (tipo: CatalogoTipo, id: number, data: { nombre?: string; activo?: boolean }) =>
    apiPut<CatalogoItem>(`/catalogos/${tipo}/${id}`, data),
  remove: (tipo: CatalogoTipo, id: number) => apiDelete<void>(`/catalogos/${tipo}/${id}`),
}
