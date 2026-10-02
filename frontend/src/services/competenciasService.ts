import { apiGet, apiPost } from '@/lib/apiClient'
import type { Competencia, TipoCompetencia } from '@/types'

export const competenciasService = {
  /** Sin `q` devuelve las primeras; con `q`, las que contienen o se parecen a lo escrito. */
  buscar: (tipo: TipoCompetencia, q?: string) =>
    apiGet<Competencia[]>('/competencias', { params: { tipo, q } }),
  /** Si ya existe una igual (salvo tildes o mayúsculas), el backend devuelve esa. */
  crear: (tipo: TipoCompetencia, nombre: string) =>
    apiPost<Competencia>('/competencias', { tipo, nombre }),
}
