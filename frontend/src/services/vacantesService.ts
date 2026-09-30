import { apiGet, apiPatch, apiPost } from '@/lib/apiClient'
import type { Vacante } from '@/types'

export const vacantesService = {
  list: () => apiGet<Vacante[]>('/vacantes'),
  create: (data: { titulo: string; cargo_id: number; descripcion: string; fecha_limite: string }) =>
    apiPost<Vacante>('/vacantes', data),
  publishLinkedIn: (id: string) => apiPost<{ linkedin_post_id: string }>(`/vacantes/${id}/publish-linkedin`),
  shareWhatsApp: (id: string) => apiGet<{ whatsapp_url: string }>(`/vacantes/${id}/share-whatsapp`),
  cerrar: (id: string) => apiPatch<Vacante>(`/vacantes/${id}/cerrar`),
}
