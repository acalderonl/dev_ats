import { apiDelete, apiGet, apiPatch, apiPost, apiPut, apiUpload } from '@/lib/apiClient'
import type {
  ConfiguracionGeneral,
  Convocatoria,
  EstadoDelPost,
  EstadoLinkedIn,
  EstadoVacante,
  Jornada,
  ParaCompartirEnLinkedIn,
  Vacante,
  VistaPreviaDelPost,
} from '@/types'

/** El ciclo de una convocatoria: hasta cuándo, en qué estado, y con qué post. */
export interface ConvocatoriaPayload {
  fecha_limite: string
  estado?: EstadoVacante
  asunto?: string | null
  post_cuerpo?: string | null
  post_imagen_url?: string | null
  post_programado_para?: string | null
}

/**
 * Las condiciones del puesto. El título no está: sale del cargo.
 * `primera_convocatoria` solo cuenta al crear: una vacante nace con su convocatoria 1.
 */
export interface VacantePayload {
  cargo_id: number
  descripcion: string
  remuneracion?: string | null
  jornada_horas?: string | null
  hora_entrada?: string | null
  hora_salida?: string | null
  tipo_contrato_id?: number | null
  campos_personalizados?: { etiqueta: string; valor: string }[]
  visibilidad?: string
  destinatarios_internos?: string[]
  primera_convocatoria?: ConvocatoriaPayload
}

interface ResultadoDePublicacion {
  post_estado: EstadoDelPost
  linkedin_post_id: string | null
  simulado: boolean
  mensaje: string
}

export const vacantesService = {
  list: () => apiGet<Vacante[]>('/vacantes'),
  create: (data: VacantePayload) => apiPost<Vacante>('/vacantes', data),
  update: (id: string, data: VacantePayload) => apiPut<Vacante>(`/vacantes/${id}`, data),
  /** Se desactiva, no se borra: tiene convocatorias y postulantes detrás. */
  toggleActiva: (id: string) => apiPatch<Vacante>(`/vacantes/${id}/toggle-activa`),
  /** Vuelve a convocar. La anterior se cierra si seguía abierta. */
  abrirConvocatoria: (id: string, data: ConvocatoriaPayload) =>
    apiPost<Convocatoria>(`/vacantes/${id}/convocatorias`, data),
  subirImagen: (file: File) => apiUpload<{ url: string }>('/vacantes/imagen', file),
  /** La misma vista previa con lo que hay escrito en el formulario, sin guardar. */
  vistaPreviaSinGuardar: (data: VacantePayload) =>
    apiPost<VistaPreviaDelPost>('/vacantes/vista-previa', data),
}

/** Todo lo que se hace con una ronda concreta y su post. */
export const convocatoriasService = {
  update: (id: string, data: ConvocatoriaPayload) => apiPut<Convocatoria>(`/convocatorias/${id}`, data),
  cambiarEstado: (id: string, estado: EstadoVacante) =>
    apiPatch<Convocatoria>(`/convocatorias/${id}/estado`, { estado }),
  cambiarEstadoDelPost: (id: string, post_estado: EstadoDelPost) =>
    apiPatch<Convocatoria>(`/convocatorias/${id}/post-estado`, { post_estado }),
  vistaPrevia: (id: string) => apiGet<VistaPreviaDelPost>(`/convocatorias/${id}/vista-previa`),
  /** Vía sin OAuth: prepara el texto y el enlace para publicar a mano. */
  compartirEnLinkedIn: (id: string) =>
    apiPost<ParaCompartirEnLinkedIn>(`/convocatorias/${id}/compartir-linkedin`),
  publicarEnLinkedIn: (id: string) =>
    apiPost<ResultadoDePublicacion>(`/convocatorias/${id}/publicar-linkedin`),
  /** Reescribe el texto del post en LinkedIn con los datos de hoy. */
  actualizarPostEnLinkedIn: (id: string) =>
    apiPatch<ResultadoDePublicacion>(`/convocatorias/${id}/linkedin-post`),
  /** Lo borra de LinkedIn y devuelve el post a borrador. */
  borrarPostEnLinkedIn: (id: string) =>
    apiDelete<ResultadoDePublicacion>(`/convocatorias/${id}/linkedin-post`),
  enviarInterno: (id: string) =>
    apiPost<{ enviados: number; mensaje: string }>(`/convocatorias/${id}/enviar-interno`),
  shareWhatsApp: (id: string) => apiGet<{ whatsapp_url: string }>(`/convocatorias/${id}/share-whatsapp`),
}

export const configuracionService = {
  leer: () => apiGet<ConfiguracionGeneral>('/configuracion'),
  guardar: (data: Partial<Record<string, string>>) => apiPut<ConfiguracionGeneral>('/configuracion', data),
  estadoLinkedIn: () => apiGet<EstadoLinkedIn>('/configuracion/linkedin/estado'),
  conectarLinkedIn: () => apiPost<{ url: string; state: string }>('/configuracion/linkedin/conectar'),
  /** Atajo sin OAuth: un token ya emitido desde el portal de LinkedIn. */
  guardarTokenLinkedIn: (access_token: string) =>
    apiPost<EstadoLinkedIn>('/configuracion/linkedin/token', { access_token }),
  terminarConexionLinkedIn: (data: { code: string; state: string }) =>
    apiPost<EstadoLinkedIn>('/configuracion/linkedin/callback', data),
  desconectarLinkedIn: () => apiDelete<void>('/configuracion/linkedin/desconectar'),
  probarCorreo: () => apiPost<{ ok: boolean; mensaje: string }>('/configuracion/correo/probar'),
  jornadas: () => apiGet<Jornada[]>('/configuracion/jornadas'),
  crearJornada: (data: { nombre: string; horas: string }) =>
    apiPost<Jornada>('/configuracion/jornadas', data),
  eliminarJornada: (id: number) => apiDelete<void>(`/configuracion/jornadas/${id}`),
}
