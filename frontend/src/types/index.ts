export type RolNombre = 'super_admin' | 'reclutador' | 'entrevistador'

export interface Usuario {
  id: string
  email: string
  nombres: string
  apellidos: string
  rol: RolNombre
  activo: boolean
  creado_en: string
}

export interface Actividad {
  texto: string
  favorita: boolean
}

/** Tramos de la barra de experiencia; el orden es el que se dibuja. */
export type ExperienciaRequerida = 'ninguna' | 'hasta_1' | '1_a_3' | '3_a_5' | 'mas_de_5'

export const EXPERIENCIA_TRAMOS: { valor: ExperienciaRequerida; etiqueta: string }[] = [
  { valor: 'ninguna', etiqueta: '0 años' },
  { valor: 'hasta_1', etiqueta: '1 año o menos' },
  { valor: '1_a_3', etiqueta: '1 a 3 años' },
  { valor: '3_a_5', etiqueta: '3 a 5 años' },
  { valor: 'mas_de_5', etiqueta: '5 años en adelante' },
]

export type TipoCompetencia = 'academico' | 'blanda'

export interface Competencia {
  id: number
  nombre: string
  tipo: TipoCompetencia
  activo: boolean
  /** En cuántos cargos se usa ya: ayuda a reutilizar la establecida en vez de crear otra. */
  usos: number
  /** 0 a 1. Solo llega al buscar: cuánto se parece a lo escrito. */
  similitud: number | null
}

export interface CompetenciaDelCargo {
  competencia_id: number
  nombre: string
  tipo: TipoCompetencia
  requerido: boolean
  deseado: boolean
}

export interface Cargo {
  id: number
  nombre_id: number
  nombre: string
  tiene_personal_a_cargo: boolean
  clasificacion_id: number | null
  clasificacion: string | null
  mision: string | null
  actividades: Actividad[]
  nivel_educacion_id: number | null
  nivel_educacion: string | null
  estado_educacion: EstadoEducacion | null
  titulo_id: number | null
  titulo: string | null
  area_academica_id: number | null
  area_academica: string | null
  experiencia_requerida: ExperienciaRequerida | null
  competencias: CompetenciaDelCargo[]
  activo: boolean
}

/** Los catálogos que alimentan los selectores del formulario de cargo. */
export type CatalogoTipo =
  | 'nombres-cargo'
  | 'clasificaciones'
  | 'niveles-educacion'
  | 'titulos'
  | 'areas-academicas'

/** Si el nivel de educación se exige terminado o basta con estar cursándolo. */
export type EstadoEducacion = 'completa' | 'en_curso'

export interface CatalogoItem {
  id: number
  nombre: string
  activo: boolean
  /** Si algún cargo lo usa; la UI lo necesita para no ofrecer un borrado que el backend rechaza. */
  en_uso: boolean
}

export type TipoRespuesta = 'multiple' | 'unica' | 'texto' | 'booleano' | 'numero'

export interface PreguntaFiltro {
  id: number
  cargo_id: number
  pregunta: string
  tipo_respuesta: TipoRespuesta
  opciones: string[] | null
  es_eliminatoria: boolean
  respuesta_correcta: string | null
}

export type EstadoVacante = 'activa' | 'expirada' | 'cerrada'

export interface Vacante {
  id: string
  titulo: string
  cargo_id: number
  descripcion: string
  documento_adjunto_url: string | null
  slug: string
  fecha_limite: string
  linkedin_post_id: string | null
  empleador_id: string
  estado: EstadoVacante
  creado_en: string
}

export interface VacantePublica {
  id: string
  titulo: string
  descripcion: string
  slug: string
  fecha_limite: string
  cargo_nombre: string
  preguntas_filtro: PreguntaFiltro[]
}

export interface FormacionSecundaria {
  institucion?: string | null
  titulo?: string | null
  anio?: number | null
}

export interface FormacionSuperior {
  institucion?: string | null
  titulo?: string | null
  estado?: string | null
}

export interface ExperienciaLaboral {
  cargo?: string | null
  empresa?: string | null
  fecha_desde?: string | null
  fecha_hasta?: string | null
  actualmente: boolean
}

export interface Postulante {
  id: string
  nombres: string
  apellidos: string
  cedula: string
  email: string
  telefono: string | null
  edad: number | null
  formacion_secundaria: FormacionSecundaria | null
  formacion_superior: FormacionSuperior | null
  nivel_instruccion: string | null
  titulos: string[] | null
  experiencia_laboral: ExperienciaLaboral[] | null
  cv_documento_url: string
  creado_en: string
}

export interface Contacto extends Postulante {
  ultimo_estado_pipeline: string | null
  ultima_vacante: string | null
  total_postulaciones: number
}

export interface CvParseado {
  nombres: string | null
  apellidos: string | null
  edad: number | null
  cedula: string | null
  email: string | null
  telefono: string | null
  formacion_secundaria: FormacionSecundaria | null
  formacion_superior: FormacionSuperior | null
  nivel_instruccion: string | null
  titulos: string[]
  experiencia_laboral: ExperienciaLaboral[]
  texto_extraido_parcial: string | null
}

export type EstadoPipeline =
  | 'pendiente_autorizacion'
  | 'postulacion_revisada'
  | 'en_revision'
  | 'preseleccionado'
  | 'evaluaciones'
  | 'entrevista'
  | 'contratado'
  | 'descartado'

export interface Postulacion {
  id: string
  vacante_id: string
  postulante_id: string
  respuestas_filtro: Record<string, string> | null
  autorizado_por: string | null
  fecha_autorizacion: string | null
  estado_pipeline: EstadoPipeline
  origen: 'LinkedIn' | 'WhatsApp' | 'Directo'
  match_score: number | null
  creado_en: string
  postulante_nombres: string
  postulante_apellidos: string
  vacante_titulo: string
}

export interface Evaluacion {
  id: string
  postulacion_id: string
  evaluador_id: string
  tipo_evaluacion: string
  puntaje: number | null
  observaciones: string | null
  creado_en: string
}

export interface DashboardMetrics {
  vacantes_activas: number
  vacantes_expiradas: number
  postulaciones_totales: number
  postulaciones_por_etapa: { estado: string; total: number }[]
  postulaciones_por_origen: { origen: string; total: number }[]
  entrevistas_pendientes: number
}
