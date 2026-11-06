import { create } from 'zustand'
import type {
  Cargo,
  CatalogoItem,
  CatalogoTipo,
  Contacto,
  EstadoDelPost,
  EstadoPipeline,
  EstadoVacante,
  Evaluacion,
  Postulacion,
  Usuario,
  Vacante,
  RolNombre,
} from '@/types'
import { cargosService, type CargoCreate } from '@/services/cargosService'
import { catalogosService } from '@/services/catalogosService'
import {
  convocatoriasService,
  vacantesService,
  type ConvocatoriaPayload,
  type VacantePayload,
} from '@/services/vacantesService'
import { postulacionesService } from '@/services/postulacionesService'
import { contactosService } from '@/services/contactosService'
import { usuariosService } from '@/services/usuariosService'

interface DataState {
  cargos: Cargo[]
  catalogos: Record<CatalogoTipo, CatalogoItem[]>
  vacantes: Vacante[]
  postulaciones: Postulacion[]
  contactos: Contacto[]
  evaluacionesPorPostulacion: Record<string, Evaluacion[]>
  usuarios: Usuario[]

  fetchCargos: () => Promise<void>
  createCargo: (data: CargoCreate) => Promise<Cargo>
  updateCargo: (id: number, data: CargoCreate) => Promise<Cargo>
  toggleCargoActivo: (id: number) => Promise<void>

  fetchCatalogo: (tipo: CatalogoTipo) => Promise<void>
  createCatalogoItem: (tipo: CatalogoTipo, nombre: string) => Promise<CatalogoItem>
  updateCatalogoItem: (
    tipo: CatalogoTipo,
    id: number,
    data: { nombre?: string; activo?: boolean }
  ) => Promise<void>
  deleteCatalogoItem: (tipo: CatalogoTipo, id: number) => Promise<void>

  fetchVacantes: () => Promise<void>
  createVacante: (data: VacantePayload) => Promise<Vacante>
  updateVacante: (id: string, data: VacantePayload) => Promise<Vacante>
  toggleActivaVacante: (id: string) => Promise<void>
  /** Vuelve a convocar la vacante; la ronda anterior se cierra si seguía abierta. */
  abrirConvocatoria: (vacanteId: string, data: ConvocatoriaPayload) => Promise<void>
  // Lo que sigue actúa sobre una **convocatoria** (su id), no sobre la vacante: el
  // ciclo y el post son de la ronda.
  actualizarConvocatoria: (convocatoriaId: string, data: ConvocatoriaPayload) => Promise<void>
  cambiarEstadoConvocatoria: (convocatoriaId: string, estado: EstadoVacante) => Promise<void>
  cambiarEstadoDelPost: (convocatoriaId: string, estado: EstadoDelPost) => Promise<void>
  publicarEnLinkedIn: (convocatoriaId: string) => Promise<{ simulado: boolean; mensaje: string }>
  enviarInterno: (convocatoriaId: string) => Promise<string>
  shareWhatsApp: (convocatoriaId: string) => Promise<string>

  fetchPostulaciones: (filters?: { vacante_id?: string }) => Promise<void>
  authorizePostulacion: (id: string) => Promise<void>
  movePostulacionStage: (id: string, estado: EstadoPipeline) => Promise<void>

  fetchContactos: (filters?: { q?: string; nivel_instruccion?: string }) => Promise<void>

  fetchEvaluaciones: (postulacionId: string) => Promise<void>
  addEvaluacion: (
    postulacionId: string,
    data: { tipo_evaluacion: string; puntaje: number; observaciones?: string }
  ) => Promise<void>

  fetchUsuarios: () => Promise<void>
  setUsuarioRol: (id: string, rol: RolNombre) => Promise<void>
  toggleUsuarioActivo: (id: string, activo: boolean) => Promise<void>
}

export const useDataStore = create<DataState>((set, get) => ({
  cargos: [],
  catalogos: {
    'nombres-cargo': [],
    clasificaciones: [],
    'niveles-educacion': [],
    titulos: [],
    'areas-academicas': [],
    'tipos-contrato': [],
  },
  vacantes: [],
  postulaciones: [],
  contactos: [],
  evaluacionesPorPostulacion: {},
  usuarios: [],

  fetchCargos: async () => set({ cargos: await cargosService.list() }),
  createCargo: async (data) => {
    const cargo = await cargosService.create(data)
    set((s) => ({ cargos: [...s.cargos, cargo] }))
    return cargo
  },
  updateCargo: async (id, data) => {
    const cargo = await cargosService.update(id, data)
    set((s) => ({ cargos: s.cargos.map((c) => (c.id === id ? cargo : c)) }))
    return cargo
  },
  toggleCargoActivo: async (id) => {
    const cargo = await cargosService.toggleActivo(id)
    set((s) => ({ cargos: s.cargos.map((c) => (c.id === id ? cargo : c)) }))
  },

  fetchCatalogo: async (tipo) => {
    const items = await catalogosService.list(tipo)
    set((s) => ({ catalogos: { ...s.catalogos, [tipo]: items } }))
  },
  createCatalogoItem: async (tipo, nombre) => {
    const item = await catalogosService.create(tipo, nombre)
    await get().fetchCatalogo(tipo)
    return item
  },
  updateCatalogoItem: async (tipo, id, data) => {
    await catalogosService.update(tipo, id, data)
    await get().fetchCatalogo(tipo)
    // El nombre o la clasificación mostrados en las tarjetas vienen del catálogo.
    await get().fetchCargos()
  },
  deleteCatalogoItem: async (tipo, id) => {
    await catalogosService.remove(tipo, id)
    await get().fetchCatalogo(tipo)
  },

  fetchVacantes: async () => set({ vacantes: await vacantesService.list() }),
  createVacante: async (data) => {
    const vacante = await vacantesService.create(data)
    set((s) => ({ vacantes: [vacante, ...s.vacantes] }))
    return vacante
  },
  updateVacante: async (id, data) => {
    const vacante = await vacantesService.update(id, data)
    set((s) => ({ vacantes: s.vacantes.map((v) => (v.id === id ? vacante : v)) }))
    return vacante
  },
  toggleActivaVacante: async (id) => {
    const vacante = await vacantesService.toggleActiva(id)
    set((s) => ({ vacantes: s.vacantes.map((v) => (v.id === id ? vacante : v)) }))
  },
  abrirConvocatoria: async (vacanteId, data) => {
    await vacantesService.abrirConvocatoria(vacanteId, data)
    await get().fetchVacantes()
  },
  // Las acciones sobre una convocatoria devuelven la convocatoria, no la vacante, así
  // que se vuelve a pedir la lista: es lo que mantiene a `convocatoria_actual` al día.
  actualizarConvocatoria: async (convocatoriaId, data) => {
    await convocatoriasService.update(convocatoriaId, data)
    await get().fetchVacantes()
  },
  cambiarEstadoConvocatoria: async (convocatoriaId, estado) => {
    await convocatoriasService.cambiarEstado(convocatoriaId, estado)
    await get().fetchVacantes()
  },
  cambiarEstadoDelPost: async (convocatoriaId, estado) => {
    await convocatoriasService.cambiarEstadoDelPost(convocatoriaId, estado)
    await get().fetchVacantes()
  },
  publicarEnLinkedIn: async (convocatoriaId) => {
    const resultado = await convocatoriasService.publicarEnLinkedIn(convocatoriaId)
    await get().fetchVacantes()
    return { simulado: resultado.simulado, mensaje: resultado.mensaje }
  },
  enviarInterno: async (convocatoriaId) => {
    const { mensaje } = await convocatoriasService.enviarInterno(convocatoriaId)
    await get().fetchVacantes()
    return mensaje
  },
  shareWhatsApp: async (convocatoriaId) => {
    const { whatsapp_url } = await convocatoriasService.shareWhatsApp(convocatoriaId)
    return whatsapp_url
  },

  fetchPostulaciones: async (filters) => set({ postulaciones: await postulacionesService.list(filters) }),
  authorizePostulacion: async (id) => {
    await postulacionesService.autorizar(id)
    await get().fetchPostulaciones()
  },
  movePostulacionStage: async (id, estado) => {
    await postulacionesService.cambiarEstado(id, estado)
    await get().fetchPostulaciones()
  },

  fetchContactos: async (filters) => set({ contactos: await contactosService.list(filters) }),

  fetchEvaluaciones: async (postulacionId) => {
    const evaluaciones = await postulacionesService.listEvaluaciones(postulacionId)
    set((s) => ({ evaluacionesPorPostulacion: { ...s.evaluacionesPorPostulacion, [postulacionId]: evaluaciones } }))
  },
  addEvaluacion: async (postulacionId, data) => {
    await postulacionesService.addEvaluacion(postulacionId, data)
    await get().fetchEvaluaciones(postulacionId)
  },

  fetchUsuarios: async () => set({ usuarios: await usuariosService.list() }),
  setUsuarioRol: async (id, rol) => {
    const usuario = await usuariosService.setRol(id, rol)
    set((s) => ({ usuarios: s.usuarios.map((u) => (u.id === id ? usuario : u)) }))
  },
  toggleUsuarioActivo: async (id, activo) => {
    const usuario = await usuariosService.setActivo(id, activo)
    set((s) => ({ usuarios: s.usuarios.map((u) => (u.id === id ? usuario : u)) }))
  },
}))
