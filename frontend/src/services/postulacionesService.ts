import { apiGet, apiPatch, apiPost } from '@/lib/apiClient'
import type { EstadoPipeline, Evaluacion, Postulacion } from '@/types'

export const postulacionesService = {
  list: (filters?: { vacante_id?: string; estado_pipeline?: string }) =>
    apiGet<Postulacion[]>('/postulaciones', { params: filters }),
  autorizar: (id: string) => apiPost<Postulacion>(`/postulaciones/${id}/autorizar`),
  cambiarEstado: (id: string, estado_pipeline: EstadoPipeline) =>
    apiPatch<Postulacion>(`/postulaciones/${id}/pipeline-status`, { estado_pipeline }),
  listEvaluaciones: (postulacionId: string) => apiGet<Evaluacion[]>(`/postulaciones/${postulacionId}/evaluaciones`),
  addEvaluacion: (postulacionId: string, data: { tipo_evaluacion: string; puntaje: number; observaciones?: string }) =>
    apiPost<Evaluacion>(`/postulaciones/${postulacionId}/evaluaciones`, data),
}
