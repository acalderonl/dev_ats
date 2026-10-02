import { apiGet, apiPatch, apiPost, apiPut } from '@/lib/apiClient'
import type { Actividad, Cargo, EstadoEducacion, ExperienciaRequerida } from '@/types'

export interface CargoCreate {
  nombre_id: number
  tiene_personal_a_cargo: boolean
  clasificacion_id: number | null
  mision: string | null
  actividades: Actividad[]
  nivel_educacion_id: number | null
  estado_educacion: EstadoEducacion | null
  titulo_id: number | null
  area_academica_id: number | null
  experiencia_requerida: ExperienciaRequerida | null
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
