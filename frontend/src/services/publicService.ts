import { apiGet, apiPost, apiUpload } from '@/lib/apiClient'
import type {
  CvExtraido,
  EducacionItem,
  ExperienciaItem,
  IdiomaItem,
  Postulante,
  RedSocial,
  VacantePublica,
} from '@/types'

/**
 * Lo que manda el formulario de postulación.
 *
 * Es el esquema de `docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx`
 * completo: los cuatro primeros campos son obligatorios y el resto va como venga,
 * porque un CV no siempre lo trae todo y obligar a rellenarlo a mano espanta al
 * candidato. Lo que sí es obligatorio aparte: aceptar la política de privacidad.
 */
export interface PostularPayload {
  nombres: string
  apellidos: string
  cedula: string
  email: string

  tipo_documento?: string | null
  fecha_nacimiento?: string | null
  genero?: string | null
  nacionalidad?: string | null
  foto_url?: string | null

  telefono_codigo_pais?: string | null
  telefono?: string | null
  telefono_tipo?: string | null
  pais_residencia?: string | null
  provincia?: string | null
  localidad?: string | null

  nivel_instruccion?: string | null
  estudios_secundarios_completos?: boolean | null
  linkedin_url?: string | null
  otras_redes?: RedSocial[]
  expectativas?: string | null
  cv_documento_url?: string | null
  edad?: number | null

  educacion?: EducacionItem[]
  idiomas?: IdiomaItem[]
  experiencia?: ExperienciaItem[]

  respuestas_filtro?: Record<string, string>
  origen?: 'LinkedIn' | 'WhatsApp' | 'Directo'
  /** 'cv' si la ficha salió de la lectura automática, 'manual' si la escribió la persona. */
  origen_datos?: 'manual' | 'cv'
  acepta_privacidad: boolean
}

export const publicService = {
  getVacante: (slug: string) => apiGet<VacantePublica>(`/public/vacantes/${slug}`),
  /** Guarda el CV y lo lee: una sola subida, porque la lectura cuesta por llamada. */
  leerCv: (file: File) => apiUpload<CvExtraido>('/public/leer-cv', file),
  subirFoto: (file: File) => apiUpload<{ url: string }>('/public/foto', file),
  /** Guarda el CV sin leerlo: para quien lo adjunta al final o lo cambia. */
  subirCv: (file: File) => apiUpload<{ url: string }>('/public/cv', file),
  postular: (slug: string, payload: PostularPayload) =>
    apiPost<Postulante>(`/public/vacantes/${slug}/postular`, payload),
}
