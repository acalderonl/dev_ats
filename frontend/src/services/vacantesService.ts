import { apiDelete, apiGet, apiPatch, apiPost, apiPut, apiUpload } from '@/lib/apiClient'
import type {
  ConfiguracionGeneral,
  EstadoDelPost,
  EstadoLinkedIn,
  EstadoVacante,
  Jornada,
  Vacante,
  VistaPreviaDelPost,
} from '@/types'

/** Lo que el formulario manda. El título no está: sale del cargo. */
export interface VacantePayload {
  cargo_id: number
  descripcion: string
  fecha_limite: string
  remuneracion?: string | null
  jornada_horas?: string | null
  hora_entrada?: string | null
  hora_salida?: string | null
  tipo_contrato_id?: number | null
  campos_personalizados?: { etiqueta: string; valor: string }[]
  asunto?: string | null
  post_cuerpo?: string | null
  post_imagen_url?: string | null
  post_programado_para?: string | null
  estado?: EstadoVacante
  visibilidad?: string
  destinatarios_internos?: string[]
}

export const vacantesService = {
  list: () => apiGet<Vacante[]>('/vacantes'),
  create: (data: VacantePayload) => apiPost<Vacante>('/vacantes', data),
  update: (id: string, data: VacantePayload) => apiPut<Vacante>(`/vacantes/${id}`, data),
  cambiarEstado: (id: string, estado: EstadoVacante) =>
    apiPatch<Vacante>(`/vacantes/${id}/estado`, { estado }),
  cambiarEstadoDelPost: (id: string, post_estado: EstadoDelPost) =>
    apiPatch<Vacante>(`/vacantes/${id}/post-estado`, { post_estado }),
  subirImagen: (file: File) => apiUpload<{ url: string }>('/vacantes/imagen', file),
  vistaPrevia: (id: string) => apiGet<VistaPreviaDelPost>(`/vacantes/${id}/vista-previa`),
  publicarEnLinkedIn: (id: string) =>
    apiPost<{ post_estado: EstadoDelPost; linkedin_post_id: string | null; simulado: boolean; mensaje: string }>(
      `/vacantes/${id}/publicar-linkedin`,
    ),
  enviarInterno: (id: string) =>
    apiPost<{ enviados: number; mensaje: string }>(`/vacantes/${id}/enviar-interno`),
  shareWhatsApp: (id: string) => apiGet<{ whatsapp_url: string }>(`/vacantes/${id}/share-whatsapp`),
}

export const configuracionService = {
  leer: () => apiGet<ConfiguracionGeneral>('/configuracion'),
  guardar: (data: Partial<Record<string, string>>) => apiPut<ConfiguracionGeneral>('/configuracion', data),
  estadoLinkedIn: () => apiGet<EstadoLinkedIn>('/configuracion/linkedin/estado'),
  conectarLinkedIn: () => apiPost<{ url: string; state: string }>('/configuracion/linkedin/conectar'),
  terminarConexionLinkedIn: (data: { code: string; state: string }) =>
    apiPost<EstadoLinkedIn>('/configuracion/linkedin/callback', data),
  desconectarLinkedIn: () => apiDelete<void>('/configuracion/linkedin/desconectar'),
  probarCorreo: () => apiPost<{ ok: boolean; mensaje: string }>('/configuracion/correo/probar'),
  jornadas: () => apiGet<Jornada[]>('/configuracion/jornadas'),
  crearJornada: (data: { nombre: string; horas: string }) =>
    apiPost<Jornada>('/configuracion/jornadas', data),
  eliminarJornada: (id: number) => apiDelete<void>(`/configuracion/jornadas/${id}`),
}
