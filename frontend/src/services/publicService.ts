import { apiGet, apiPost, apiUpload } from '@/lib/apiClient'
import type { CvParseado, ExperienciaLaboral, FormacionSecundaria, FormacionSuperior, Postulante, VacantePublica } from '@/types'

export interface PostularPayload {
  nombres: string
  apellidos: string
  cedula: string
  email: string
  telefono?: string
  edad?: number
  formacion_secundaria?: FormacionSecundaria
  formacion_superior?: FormacionSuperior
  nivel_instruccion?: string
  titulos?: string[]
  experiencia_laboral?: ExperienciaLaboral[]
  respuestas_filtro?: Record<string, string>
  origen?: 'LinkedIn' | 'WhatsApp' | 'Directo'
}

export const publicService = {
  getVacante: (slug: string) => apiGet<VacantePublica>(`/public/vacantes/${slug}`),
  parseCv: (file: File) => apiUpload<CvParseado>('/public/parse-cv', file),
  postular: (slug: string, payload: PostularPayload) =>
    apiPost<Postulante>(`/public/vacantes/${slug}/postular`, payload),
}
