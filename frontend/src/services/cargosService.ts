import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/apiClient'
import type { Cargo, PreguntaFiltro, TipoRespuesta } from '@/types'

export const cargosService = {
  list: () => apiGet<Cargo[]>('/cargos'),
  create: (data: { nombre: string; departamento?: string; descripcion?: string }) =>
    apiPost<Cargo>('/cargos', data),
  toggleActivo: (id: number) => apiPatch<Cargo>(`/cargos/${id}/toggle-activo`),
  listPreguntas: (cargoId: number) => apiGet<PreguntaFiltro[]>(`/cargos/${cargoId}/preguntas-filtro`),
  addPregunta: (
    cargoId: number,
    data: { pregunta: string; tipo_respuesta: TipoRespuesta; es_eliminatoria: boolean; opciones?: string[] | null }
  ) => apiPost<PreguntaFiltro>(`/cargos/${cargoId}/preguntas-filtro`, data),
  removePregunta: (preguntaId: number) => apiDelete<void>(`/cargos/preguntas-filtro/${preguntaId}`),
}
