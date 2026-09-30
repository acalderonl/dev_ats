import { create } from 'zustand'
import type {
  Cargo,
  Contacto,
  EstadoPipeline,
  Evaluacion,
  PreguntaFiltro,
  Postulacion,
  TipoRespuesta,
  Usuario,
  Vacante,
  RolNombre,
} from '@/types'
import { cargosService } from '@/services/cargosService'
import { vacantesService } from '@/services/vacantesService'
import { postulacionesService } from '@/services/postulacionesService'
import { contactosService } from '@/services/contactosService'
import { usuariosService } from '@/services/usuariosService'

interface DataState {
  cargos: Cargo[]
  preguntasPorCargo: Record<number, PreguntaFiltro[]>
  vacantes: Vacante[]
  postulaciones: Postulacion[]
  contactos: Contacto[]
  evaluacionesPorPostulacion: Record<string, Evaluacion[]>
  usuarios: Usuario[]

  fetchCargos: () => Promise<void>
  createCargo: (data: { nombre: string; departamento?: string; descripcion?: string }) => Promise<Cargo>
  toggleCargoActivo: (id: number) => Promise<void>
  fetchPreguntas: (cargoId: number) => Promise<void>
  addPregunta: (
    cargoId: number,
    data: { pregunta: string; tipo_respuesta: TipoRespuesta; es_eliminatoria: boolean }
  ) => Promise<void>
  removePregunta: (cargoId: number, preguntaId: number) => Promise<void>

  fetchVacantes: () => Promise<void>
  createVacante: (data: { titulo: string; cargo_id: number; descripcion: string; fecha_limite: string }) => Promise<Vacante>
  publishLinkedIn: (id: string) => Promise<void>
  shareWhatsApp: (id: string) => Promise<string>
  cerrarVacante: (id: string) => Promise<void>

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
  preguntasPorCargo: {},
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
  toggleCargoActivo: async (id) => {
    const cargo = await cargosService.toggleActivo(id)
    set((s) => ({ cargos: s.cargos.map((c) => (c.id === id ? cargo : c)) }))
  },
  fetchPreguntas: async (cargoId) => {
    const preguntas = await cargosService.listPreguntas(cargoId)
    set((s) => ({ preguntasPorCargo: { ...s.preguntasPorCargo, [cargoId]: preguntas } }))
  },
  addPregunta: async (cargoId, data) => {
    await cargosService.addPregunta(cargoId, data)
    await get().fetchPreguntas(cargoId)
  },
  removePregunta: async (cargoId, preguntaId) => {
    await cargosService.removePregunta(preguntaId)
    await get().fetchPreguntas(cargoId)
  },

  fetchVacantes: async () => set({ vacantes: await vacantesService.list() }),
  createVacante: async (data) => {
    const vacante = await vacantesService.create(data)
    set((s) => ({ vacantes: [vacante, ...s.vacantes] }))
    return vacante
  },
  publishLinkedIn: async (id) => {
    await vacantesService.publishLinkedIn(id)
    await get().fetchVacantes()
  },
  shareWhatsApp: async (id) => {
    const { whatsapp_url } = await vacantesService.shareWhatsApp(id)
    return whatsapp_url
  },
  cerrarVacante: async (id) => {
    await vacantesService.cerrar(id)
    await get().fetchVacantes()
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
