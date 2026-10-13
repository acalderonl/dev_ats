import { apiGet, apiPatch, apiPost, apiPut } from '@/lib/apiClient'
import type { Actividad, Cargo, EstadoEducacion, ExperienciaRequerida } from '@/types'

export interface CargoCreate {
  nombre_id: number
  tiene_personal_a_cargo: boolean
  clasificacion_id: number | null
  mision: string | null
  actividades: Actividad[]
  niveles_educacion: { nivel_id: number; estado: EstadoEducacion }[]
  titulos_ids: number[]
  areas_academicas_ids: number[]
  experiencia_requerida: ExperienciaRequerida | null
  experiencia_empresas_similares: boolean
  experiencia_cargos_similares: boolean
  experiencia_interna_otros_cargos: boolean
  competencias: { competencia_id: number; requerido: boolean; deseado: boolean }[]
}

export const cargosService = {
  list: () => apiGet<Cargo[]>('/cargos'),
  create: (data: CargoCreate) => apiPost<Cargo>('/cargos', data),
  update: (id: number, data: CargoCreate) => apiPut<Cargo>(`/cargos/${id}`, data),
  toggleActivo: (id: number) => apiPatch<Cargo>(`/cargos/${id}/toggle-activo`),
  // La gestión de preguntas filtro ya no se hace desde Cargos. Los endpoints siguen vivos en
  // el backend: el portal del candidato lee las preguntas al abrir una vacante.
}
