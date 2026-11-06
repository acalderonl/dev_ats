import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/lib/apiClient'
import type { Permiso, PermisosDeUsuario, Rol, RolNombre, Usuario } from '@/types'

export interface UsuarioCreate {
  email: string
  nombres: string
  apellidos: string
  password: string
  rol: string
  activo?: boolean
}

export interface UsuarioUpdate {
  email?: string
  nombres?: string
  apellidos?: string
  rol?: string
  activo?: boolean
}

export const usuariosService = {
  list: () => apiGet<Usuario[]>('/users'),
  create: (data: UsuarioCreate) => apiPost<Usuario>('/users', data),
  update: (id: string, data: UsuarioUpdate) => apiPut<Usuario>(`/users/${id}`, data),
  setRol: (id: string, rol: RolNombre) => apiPut<Usuario>(`/users/${id}/role`, { rol }),
  setActivo: (id: string, activo: boolean) => apiPatch<Usuario>(`/users/${id}/activo`, { activo }),
  restablecerClave: (id: string, password: string) =>
    apiPut<void>(`/users/${id}/password`, { password }),

  permisosDe: (id: string) => apiGet<PermisosDeUsuario>(`/users/${id}/permisos`),
  ajustarPermisos: (id: string, ajustes: { clave: string; concedido: boolean }[]) =>
    apiPut<PermisosDeUsuario>(`/users/${id}/permisos`, ajustes),
  /** Los permisos de quien está dentro: con esto se pinta el menú. */
  mios: () => apiGet<string[]>('/users/yo/permisos'),
}

export const rolesService = {
  list: () => apiGet<Rol[]>('/roles'),
  catalogoDePermisos: () => apiGet<Permiso[]>('/roles/permisos'),
  create: (data: { nombre: string; descripcion?: string | null; permisos: string[] }) =>
    apiPost<Rol>('/roles', data),
  update: (
    id: number,
    data: { nombre?: string; descripcion?: string | null; activo?: boolean; permisos?: string[] },
  ) => apiPut<Rol>(`/roles/${id}`, data),
  remove: (id: number) => apiDelete<void>(`/roles/${id}`),
}
