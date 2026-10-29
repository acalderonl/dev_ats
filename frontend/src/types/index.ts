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
  niveles_educacion: NivelDelCargo[]
  titulos: ItemDeEducacion[]
  areas_academicas: ItemDeEducacion[]
  experiencia_requerida: ExperienciaRequerida | null
  experiencia_empresas_similares: boolean
  experiencia_cargos_similares: boolean
  experiencia_interna_otros_cargos: boolean
  competencias: CompetenciaDelCargo[]
  activo: boolean
}

/** Los catálogos que alimentan los selectores de los formularios. */
export type CatalogoTipo =
  | 'nombres-cargo'
  | 'clasificaciones'
  | 'niveles-educacion'
  | 'titulos'
  | 'areas-academicas'
  | 'tipos-contrato'

/** Si el nivel de educación se exige terminado o basta con estar cursándolo. */
export type EstadoEducacion = 'completa' | 'en_curso'

/** Tope de la sección 4: como mucho dos niveles, dos títulos y dos áreas por cargo. */
export const MAXIMO_EDUCACION = 2

/** Un nivel exigido por el cargo, con su propio estado. */
export interface NivelDelCargo {
  nivel_id: number
  estado: EstadoEducacion
  nombre: string
}

/** Un título o un área ya elegidos por el cargo. */
export interface ItemDeEducacion {
  id: number
  nombre: string
}

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

export type EstadoVacante = "borrador" | "abierta" | "cerrada"
/** "compartido" no es "publicado": al abrir el compositor entregamos el contenido,
 *  pero quien pulsa Publicar es la persona y el sistema no puede saberlo. */
export type EstadoDelPost = "borrador" | "programado" | "compartido" | "publicado" | "error"
export type VisibilidadVacante = "publica" | "interna" | "mixta"

export interface CampoPersonalizado {
  etiqueta: string
  valor: string
}

export interface Vacante {
  id: string
  cargo_id: number
  titulo: string
  descripcion: string
  slug: string
  fecha_limite: string

  remuneracion: string | null
  jornada_horas: string | null
  hora_entrada: string | null
  hora_salida: string | null
  tipo_contrato_id: number | null
  tipo_contrato_nombre: string | null
  campos_personalizados: CampoPersonalizado[]

  asunto: string | null
  post_cuerpo: string | null
  post_imagen_url: string | null
  post_programado_para: string | null
  post_estado: EstadoDelPost
  post_publicado_en: string | null
  post_error: string | null
  linkedin_post_id: string | null

  visibilidad: VisibilidadVacante
  destinatarios_internos: string[]
  enviado_internamente_en: string | null

  url_publica: string | null
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
  remuneracion: string | null
  hora_entrada: string | null
  hora_salida: string | null
  tipo_contrato: string | null
  campos_personalizados: CampoPersonalizado[]
  preguntas_filtro: PreguntaFiltro[]
}

export interface VistaPreviaDelPost {
  asunto: string
  cuerpo: string
  imagen_url: string | null
  enlace_para_postular: string
  visibilidad: VisibilidadVacante
  destinatarios_internos: string[]
  programado_para: string | null
  caracteres: number
}

export interface Jornada {
  id: number
  nombre: string
  horas: string
  activo: boolean
}

/** Cómo se conecta el sistema para enviar correo. */
export type TipoDeCorreo = 'gmail' | 'smtp'
export type CifradoSmtp = 'ssl' | 'starttls' | 'ninguna'

export interface ConfiguracionGeneral {
  empresa_nombre: string | null
  linkedin_client_id: string | null
  linkedin_redirect_uri: string | null
  correo_tipo: TipoDeCorreo | null
  gmail_remitente: string | null
  smtp_servidor: string | null
  smtp_puerto: string | null
  smtp_cifrado: CifradoSmtp | null
  smtp_usuario: string | null
  smtp_remitente: string | null
  dominios_corporativos: string | null
  linkedin_client_secret_configurado: boolean
  linkedin_client_secret_pista: string | null
  gmail_password_app_configurado: boolean
  gmail_password_app_pista: string | null
  smtp_password_configurado: boolean
  smtp_password_pista: string | null
}

export interface EstadoLinkedIn {
  credenciales_configuradas: boolean
  cuenta_conectada: boolean
  nombre_en_linkedin: string | null
  expira_en: string | null
  correo_configurado: boolean
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

// --- Roles y permisos ---

export interface Permiso {
  id: number
  clave: string
  modulo: string
  accion: string
  etiqueta: string
}

export interface Rol {
  id: number
  nombre: string
  descripcion: string | null
  es_sistema: boolean
  activo: boolean
  permisos: string[]
  usuarios_asignados: number
}

/** Lo que la pantalla necesita para pintar las casillas sin adivinar. */
export interface PermisosDeUsuario {
  rol: string
  es_super_admin: boolean
  /** Lo que trae su rol de fábrica. */
  del_rol: string[]
  /** Las excepciones puestas a esta persona: clave -> concedido. */
  ajustes: Record<string, boolean>
  /** El resultado de aplicar unas sobre otras. */
  efectivos: string[]
}

/** Una competencia que otros cargos ya usan, con cuántos la usan. */
export interface CompetenciaSugerida {
  id: number
  nombre: string
  usos: number
}

/** Lo que piden los cargos de una misma clasificación. */
export interface GrupoPorClasificacion {
  clasificacion_id: number | null
  clasificacion: string
  competencias: CompetenciaSugerida[]
}

/** Lo que hace falta para llevar una vacante a LinkedIn a mano. */
export interface ParaCompartirEnLinkedIn {
  texto: string
  enlace_de_la_vacante: string
  url_del_compositor: string
  aviso: string
}

// --- Ficha del candidato: el esquema de `docs/resouces/ESQUEMA FORMULARIO...` ---

/** Una fila de educación. Fechas en mes + año porque un CV rara vez trae el día. */
export interface EducacionItem {
  titulo: string | null
  pais: string | null
  institucion: string | null
  area_estudio: string | null
  nivel_estudio: string | null
  estado_estudio: string | null
  inicio_mes: number | null
  inicio_anio: number | null
  actualmente: boolean
  fin_mes: number | null
  fin_anio: number | null
  descripcion: string | null
}

export interface IdiomaItem {
  idioma: string
  nivel_escrito: string | null
  nivel_oral: string | null
}

export interface ExperienciaItem {
  puesto: string | null
  jerarquia: string | null
  empresa: string | null
  pais: string | null
  industria: string | null
  area_trabajo: string | null
  subarea_trabajo: string | null
  inicio_mes: number | null
  inicio_anio: number | null
  actualmente: boolean
  fin_mes: number | null
  fin_anio: number | null
  descripcion: string | null
}

export interface RedSocial {
  red: string
  url: string
}

/** Lo que devuelve la lectura del CV: los mismos campos del formulario, más cómo fue. */
export interface CvExtraido {
  nombres: string | null
  apellidos: string | null
  email: string | null
  tipo_documento: string | null
  numero_documento: string | null
  fecha_nacimiento: string | null
  telefono_codigo_pais: string | null
  telefono: string | null
  telefono_tipo: string | null
  genero: string | null
  nacionalidad: string | null
  pais_residencia: string | null
  provincia: string | null
  localidad: string | null
  estudios_secundarios_completos: boolean | null
  linkedin_url: string | null
  otras_redes: RedSocial[]
  educacion: EducacionItem[]
  idiomas: IdiomaItem[]
  experiencia: ExperienciaItem[]
  /** 'claude', 'heuristicas' o 'vacio': distingue "el CV no lo decía" de "no hay lector". */
  motor: string
  aviso: string | null
  campos_encontrados: number
  cv_documento_url: string | null
}
