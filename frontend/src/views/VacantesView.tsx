import { useEffect, useMemo, useState } from 'react'
import {
  Calendar,
  Copy,
  Eye,
  Image as ImageIcon,
  Linkedin,
  Loader2,
  Mail,
  MessageCircle,
  Plus,
  Send,
  Settings2,
  Trash2,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { GestionCatalogoModal } from '@/components/catalogo/GestionCatalogoModal'
import { CamposPersonalizados } from '@/components/vacantes/CamposPersonalizados'
import { SelectorDeHorario } from '@/components/vacantes/SelectorDeHorario'
import { useDataStore } from '@/store/dataStore'
import { useAuthStore } from '@/store/authStore'
import { configuracionService, vacantesService } from '@/services/vacantesService'
import { ApiError } from '@/lib/apiClient'
import type {
  CampoPersonalizado,
  EstadoVacante,
  Jornada,
  Vacante,
  VisibilidadVacante,
  VistaPreviaDelPost,
} from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

interface FormularioDeVacante {
  cargo_id: number
  descripcion: string
  fecha_limite: string
  remuneracion: string
  jornada_horas: string
  hora_entrada: string
  hora_salida: string
  tipo_contrato_id: number | null
  campos_personalizados: CampoPersonalizado[]
  asunto: string
  post_cuerpo: string
  post_imagen_url: string | null
  post_programado_para: string
  estado: EstadoVacante
  visibilidad: VisibilidadVacante
  destinatarios_internos: string
}

const FORM_VACIO: FormularioDeVacante = {
  cargo_id: 0,
  descripcion: '',
  fecha_limite: '',
  remuneracion: '',
  jornada_horas: '',
  hora_entrada: '',
  hora_salida: '',
  tipo_contrato_id: null,
  campos_personalizados: [],
  asunto: '',
  post_cuerpo: '',
  post_imagen_url: null,
  post_programado_para: '',
  estado: 'borrador',
  visibilidad: 'publica',
  destinatarios_internos: '',
}

/** Un `datetime` del backend al formato que entiende `<input type="datetime-local">`. */
function aInputLocal(iso: string | null): string {
  if (!iso) return ''
  const fecha = new Date(iso)
  const desfase = fecha.getTimezoneOffset() * 60000
  return new Date(fecha.getTime() - desfase).toISOString().slice(0, 16)
}

function formDesdeVacante(v: Vacante): FormularioDeVacante {
  return {
    cargo_id: v.cargo_id,
    descripcion: v.descripcion,
    fecha_limite: aInputLocal(v.fecha_limite),
    remuneracion: v.remuneracion ?? '',
    jornada_horas: v.jornada_horas ?? '',
    hora_entrada: v.hora_entrada?.slice(0, 5) ?? '',
    hora_salida: v.hora_salida?.slice(0, 5) ?? '',
    tipo_contrato_id: v.tipo_contrato_id,
    campos_personalizados: v.campos_personalizados ?? [],
    asunto: v.asunto ?? '',
    post_cuerpo: v.post_cuerpo ?? '',
    post_imagen_url: v.post_imagen_url,
    post_programado_para: aInputLocal(v.post_programado_para),
    estado: v.estado,
    visibilidad: v.visibilidad,
    destinatarios_internos: (v.destinatarios_internos ?? []).join(', '),
  }
}

function Seccion({ numero, titulo, children }: { numero: number; titulo: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
          {numero}
        </span>
        <h3 className="text-sm font-semibold text-slate-800">{titulo}</h3>
      </div>
      {children}
    </section>
  )
}

const TONO_DE_ESTADO: Record<EstadoVacante, 'slate' | 'green' | 'red'> = {
  borrador: 'slate',
  abierta: 'green',
  cerrada: 'red',
}

const ETIQUETA_DEL_POST: Record<string, string> = {
  borrador: 'Post en borrador',
  programado: 'Post programado',
  publicado: 'Post publicado',
  error: 'Post con error',
}

export function VacantesView() {
  const {
    vacantes,
    cargos,
    postulaciones,
    catalogos,
    fetchVacantes,
    fetchCargos,
    fetchPostulaciones,
    fetchCatalogo,
    createVacante,
    updateVacante,
    cambiarEstadoVacante,
    publicarEnLinkedIn,
    enviarInterno,
    shareWhatsApp,
  } = useDataStore()
  const user = useAuthStore((s) => s.user)
  const esAdmin = user?.rol === 'super_admin'

  const [loading, setLoading] = useState(true)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [enEdicion, setEnEdicion] = useState<Vacante | null>(null)
  const [form, setForm] = useState<FormularioDeVacante>(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [subiendoImagen, setSubiendoImagen] = useState(false)
  const [gestionandoContratos, setGestionandoContratos] = useState(false)
  const [jornadas, setJornadas] = useState<Jornada[]>([])
  const [previa, setPrevia] = useState<VistaPreviaDelPost | null>(null)
  const [publicandoId, setPublicandoId] = useState<string | null>(null)

  const tiposContrato = catalogos['tipos-contrato'] ?? []
  const cargosActivos = useMemo(() => cargos.filter((c) => c.activo), [cargos])

  useEffect(() => {
    Promise.all([
      fetchVacantes(),
      fetchCargos(),
      fetchPostulaciones(),
      fetchCatalogo('tipos-contrato'),
      configuracionService.jornadas().then(setJornadas),
    ])
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchVacantes, fetchCargos, fetchPostulaciones, fetchCatalogo])

  function abrirNueva() {
    setEnEdicion(null)
    setForm({ ...FORM_VACIO, cargo_id: cargosActivos[0]?.id ?? 0 })
    setModalAbierto(true)
  }

  function abrirEdicion(vacante: Vacante) {
    setEnEdicion(vacante)
    setForm(formDesdeVacante(vacante))
    setModalAbierto(true)
  }

  function cerrarModal() {
    setModalAbierto(false)
    setEnEdicion(null)
  }

  function actualizar(cambios: Partial<FormularioDeVacante>) {
    setForm((f) => ({ ...f, ...cambios }))
  }

  const correosInternos = useMemo(
    () =>
      form.destinatarios_internos
        .split(/[,\n;]/)
        .map((c) => c.trim())
        .filter(Boolean),
    [form.destinatarios_internos],
  )

  const necesitaCorreos = form.visibilidad !== 'publica'

  async function subirImagen(archivo: File) {
    setSubiendoImagen(true)
    try {
      const { url } = await vacantesService.subirImagen(archivo)
      actualizar({ post_imagen_url: url })
      toast.success('Imagen cargada')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSubiendoImagen(false)
    }
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault()
    if (!form.cargo_id) return toast.error('Elige el cargo de la vacante')
    if (!form.fecha_limite) return toast.error('Falta la fecha límite')
    if (necesitaCorreos && correosInternos.length === 0) {
      return toast.error('Una vacante interna o mixta necesita al menos un correo destinatario')
    }

    const payload = {
      cargo_id: Number(form.cargo_id),
      descripcion: form.descripcion,
      fecha_limite: new Date(form.fecha_limite).toISOString(),
      remuneracion: form.remuneracion || null,
      jornada_horas: form.jornada_horas || null,
      hora_entrada: form.hora_entrada || null,
      hora_salida: form.hora_salida || null,
      tipo_contrato_id: form.tipo_contrato_id,
      campos_personalizados: form.campos_personalizados.filter((c) => c.etiqueta.trim()),
      asunto: form.asunto || null,
      post_cuerpo: form.post_cuerpo || null,
      post_imagen_url: form.post_imagen_url,
      post_programado_para: form.post_programado_para
        ? new Date(form.post_programado_para).toISOString()
        : null,
      estado: form.estado,
      visibilidad: form.visibilidad,
      destinatarios_internos: correosInternos,
    }

    setGuardando(true)
    try {
      const vacante = enEdicion
        ? await updateVacante(enEdicion.id, payload)
        : await createVacante(payload)
      toast.success(enEdicion ? 'Vacante actualizada' : `Vacante "${vacante.titulo}" creada`)
      cerrarModal()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function verVistaPrevia(vacante: Vacante) {
    try {
      setPrevia(await vacantesService.vistaPrevia(vacante.id))
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function publicar(vacante: Vacante) {
    setPublicandoId(vacante.id)
    try {
      const { simulado, mensaje } = await publicarEnLinkedIn(vacante.id)
      if (simulado) toast.warning(mensaje)
      else toast.success(mensaje)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  async function enviar(vacante: Vacante) {
    setPublicandoId(vacante.id)
    try {
      toast.success(await enviarInterno(vacante.id))
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  function copiarEnlace(vacante: Vacante) {
    const url = vacante.url_publica ?? `${window.location.origin}/postular/${vacante.slug}`
    navigator.clipboard?.writeText(url)
    toast.success('Enlace copiado')
  }

  async function compartirWhatsApp(id: string) {
    try {
      window.open(await shareWhatsApp(id), '_blank')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Vacantes</h1>
          <p className="text-sm text-slate-500">
            Un cargo puesto en circulación. Pulsa una tarjeta para editarla.
          </p>
        </div>
        <button
          onClick={abrirNueva}
          className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={16} />
          Nueva Vacante
        </button>
      </div>

      {vacantes.length === 0 && (
        <Card>
          <p className="py-8 text-center text-sm text-slate-500">
            Todavía no hay vacantes. Crea una desde un cargo existente.
          </p>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {vacantes.map((vacante) => {
          const postulantes = postulaciones.filter((p) => p.vacante_id === vacante.id).length
          return (
            <Card key={vacante.id}>
              <div
                role="button"
                tabIndex={0}
                onClick={() => abrirEdicion(vacante)}
                onKeyDown={(e) => e.key === 'Enter' && abrirEdicion(vacante)}
                className="cursor-pointer space-y-3"
                title="Abrir para ver o modificar esta vacante"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-slate-900">{vacante.titulo}</h3>
                  <div className="flex shrink-0 gap-1.5">
                    <Badge tone={TONO_DE_ESTADO[vacante.estado]}>{vacante.estado}</Badge>
                    <Badge tone={vacante.visibilidad === 'publica' ? 'blue' : 'slate'}>
                      {vacante.visibilidad}
                    </Badge>
                  </div>
                </div>

                <p className="line-clamp-2 text-sm text-slate-600">{vacante.descripcion}</p>

                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  {vacante.remuneracion && <span>${Number(vacante.remuneracion).toFixed(2)}</span>}
                  {vacante.hora_entrada && vacante.hora_salida && (
                    <span>
                      {vacante.hora_entrada.slice(0, 5)} – {vacante.hora_salida.slice(0, 5)}
                    </span>
                  )}
                  {vacante.tipo_contrato_nombre && <span>{vacante.tipo_contrato_nombre}</span>}
                  <span>{postulantes} postulante(s)</span>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span
                    className={
                      vacante.post_estado === 'error'
                        ? 'text-red-600'
                        : vacante.post_estado === 'publicado'
                          ? 'text-green-600'
                          : 'text-slate-500'
                    }
                  >
                    {ETIQUETA_DEL_POST[vacante.post_estado]}
                  </span>
                  {vacante.post_programado_para && vacante.post_estado === 'programado' && (
                    <span className="text-slate-400">
                      · {new Date(vacante.post_programado_para).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
                <button
                  onClick={() => verVistaPrevia(vacante)}
                  className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  <Eye size={13} /> Vista previa
                </button>
                <button
                  onClick={() => copiarEnlace(vacante)}
                  className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  <Copy size={13} /> Enlace
                </button>
                {vacante.visibilidad !== 'interna' && (
                  <button
                    onClick={() => publicar(vacante)}
                    disabled={publicandoId === vacante.id}
                    className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                  >
                    {publicandoId === vacante.id ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Linkedin size={13} />
                    )}
                    LinkedIn
                  </button>
                )}
                {vacante.visibilidad !== 'publica' && (
                  <button
                    onClick={() => enviar(vacante)}
                    disabled={publicandoId === vacante.id}
                    className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                  >
                    <Mail size={13} /> Enviar interno
                  </button>
                )}
                <button
                  onClick={() => compartirWhatsApp(vacante.id)}
                  className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  <MessageCircle size={13} /> WhatsApp
                </button>
                {vacante.estado !== 'cerrada' && (
                  <button
                    onClick={() => cambiarEstadoVacante(vacante.id, 'cerrada').catch((e) => toast.error(errorMessage(e)))}
                    className="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
                  >
                    Cerrar
                  </button>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* ------------------------------------------------------------ Formulario */}
      <Modal
        open={modalAbierto}
        onClose={cerrarModal}
        title={enEdicion ? `Editar: ${enEdicion.titulo}` : 'Nueva Vacante'}
        wide
        confirmarCierre="Se perderá lo que hayas escrito en el formulario."
      >
        <form onSubmit={guardar} className="space-y-6">
          <Seccion numero={1} titulo="Cargo de la vacante">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Cargo *</label>
              <select
                required
                value={form.cargo_id}
                onChange={(e) => actualizar({ cargo_id: Number(e.target.value) })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value={0}>Selecciona...</option>
                {cargosActivos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-500">
                El título de la vacante es el nombre del cargo. Solo aparecen los cargos activos.
              </p>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Descripción</label>
              <textarea
                rows={3}
                value={form.descripcion}
                onChange={(e) => actualizar({ descripcion: e.target.value })}
                placeholder="Qué se busca y por qué merece la pena este puesto."
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Fecha límite *</label>
              <input
                type="datetime-local"
                required
                value={form.fecha_limite}
                onChange={(e) => actualizar({ fecha_limite: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </Seccion>

          <Seccion numero={2} titulo="Remuneración">
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-500">
                $
              </span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.remuneracion}
                onChange={(e) => actualizar({ remuneracion: e.target.value })}
                onBlur={(e) =>
                  actualizar({ remuneracion: e.target.value ? Number(e.target.value).toFixed(2) : '' })
                }
                placeholder="0.00"
                className="w-full rounded-lg border border-slate-300 py-2 pl-7 pr-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </Seccion>

          <Seccion numero={3} titulo="Horario">
            <SelectorDeHorario
              jornadas={jornadas}
              jornadaHoras={form.jornada_horas}
              horaEntrada={form.hora_entrada}
              horaSalida={form.hora_salida}
              onChange={(c) =>
                actualizar({
                  ...(c.jornadaHoras !== undefined && { jornada_horas: c.jornadaHoras }),
                  ...(c.horaEntrada !== undefined && { hora_entrada: c.horaEntrada }),
                  ...(c.horaSalida !== undefined && { hora_salida: c.horaSalida }),
                })
              }
              puedeConfigurar={esAdmin}
            />
          </Seccion>

          <Seccion numero={4} titulo="Tipo de contrato">
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="text-sm font-medium text-slate-700">Tipo de contrato</label>
                <button
                  type="button"
                  onClick={() => setGestionandoContratos(true)}
                  title="Administrar tipos de contrato"
                  className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <Settings2 size={15} />
                </button>
              </div>
              <select
                value={form.tipo_contrato_id ?? ''}
                onChange={(e) =>
                  actualizar({ tipo_contrato_id: e.target.value ? Number(e.target.value) : null })
                }
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">Selecciona...</option>
                {tiposContrato
                  .filter((t) => t.activo)
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nombre}
                    </option>
                  ))}
              </select>
            </div>
          </Seccion>

          <Seccion numero={5} titulo="Campos adicionales">
            <CamposPersonalizados
              campos={form.campos_personalizados}
              onChange={(campos_personalizados) => actualizar({ campos_personalizados })}
            />
          </Seccion>

          <Seccion numero={6} titulo="La publicación">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Asunto del post</label>
              <input
                value={form.asunto}
                onChange={(e) => actualizar({ asunto: e.target.value })}
                placeholder="El titular con el que se verá la publicación"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Texto del post</label>
              <textarea
                rows={3}
                value={form.post_cuerpo}
                onChange={(e) => actualizar({ post_cuerpo: e.target.value })}
                placeholder="Si lo dejas vacío se usa la descripción de la vacante."
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            {enEdicion && (
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs font-medium text-slate-600">Enlace para postular</p>
                <div className="mt-1 flex items-center gap-2">
                  <code className="flex-1 truncate text-xs text-slate-500">
                    {enEdicion.url_publica ?? `${window.location.origin}/postular/${enEdicion.slug}`}
                  </code>
                  <button
                    type="button"
                    onClick={() => copiarEnlace(enEdicion)}
                    className="rounded-md p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-600"
                  >
                    <Copy size={14} />
                  </button>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Lo genera la aplicación y no cambia aunque edites la vacante.
                </p>
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Imagen del post</label>
              {form.post_imagen_url ? (
                <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-2">
                  <img
                    src={form.post_imagen_url}
                    alt="Imagen del post"
                    className="h-16 w-16 rounded object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => actualizar({ post_imagen_url: null })}
                    className="flex items-center gap-1 text-xs text-red-600 hover:underline"
                  >
                    <Trash2 size={13} /> Quitar
                  </button>
                </div>
              ) : (
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 py-4 text-sm text-slate-500 hover:border-brand-400 hover:text-brand-600">
                  {subiendoImagen ? <Loader2 size={16} className="animate-spin" /> : <ImageIcon size={16} />}
                  {subiendoImagen ? 'Subiendo...' : 'JPG, PNG, GIF o WebP (máx. 5 MB)'}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    className="hidden"
                    onChange={(e) => {
                      const archivo = e.target.files?.[0]
                      if (archivo) subirImagen(archivo)
                      e.target.value = ''
                    }}
                  />
                </label>
              )}
            </div>

            <div>
              <label className="mb-1 flex items-center gap-1.5 text-sm font-medium text-slate-700">
                <Calendar size={14} /> Programar publicación
              </label>
              <input
                type="datetime-local"
                value={form.post_programado_para}
                onChange={(e) => actualizar({ post_programado_para: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <p className="mt-1 text-xs text-amber-600">
                La fecha se guarda, pero todavía no hay nada que publique solo a esa hora: hay que
                pulsar LinkedIn. Queda pendiente el proceso que lo haga.
              </p>
            </div>
          </Seccion>

          <Seccion numero={7} titulo="Alcance y estado">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Quién puede verla</label>
              <div className="grid grid-cols-3 gap-2">
                {(['publica', 'interna', 'mixta'] as VisibilidadVacante[]).map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => actualizar({ visibilidad: v })}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium capitalize ${
                      form.visibilidad === v
                        ? 'border-brand-500 bg-brand-50 text-brand-700'
                        : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {form.visibilidad === 'publica' && 'Se comparte por donde quieras y sale en el portal.'}
                {form.visibilidad === 'interna' &&
                  'Solo por correo corporativo. No aparece en el portal público aunque tengan el enlace.'}
                {form.visibilidad === 'mixta' && 'Las dos cosas: portal público y envío interno.'}
              </p>
            </div>

            {necesitaCorreos && (
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Correos corporativos *
                </label>
                <textarea
                  rows={2}
                  value={form.destinatarios_internos}
                  onChange={(e) => actualizar({ destinatarios_internos: e.target.value })}
                  placeholder="persona@empresa.com, otra@empresa.com"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <p className="mt-1 text-xs text-slate-500">
                  {correosInternos.length} destinatario(s). Separa con comas o saltos de línea.
                </p>
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Estado de la vacante</label>
              <div className="grid grid-cols-3 gap-2">
                {(['borrador', 'abierta', 'cerrada'] as EstadoVacante[]).map((e) => (
                  <button
                    key={e}
                    type="button"
                    onClick={() => actualizar({ estado: e })}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium capitalize ${
                      form.estado === e
                        ? 'border-brand-500 bg-brand-50 text-brand-700'
                        : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Solo una vacante <strong>abierta</strong> recibe postulaciones. Un borrador no se ve
                desde fuera.
              </p>
            </div>
          </Seccion>

          <button
            type="submit"
            disabled={guardando}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {guardando && <Loader2 size={15} className="animate-spin" />}
            {enEdicion ? 'Guardar cambios' : 'Crear Vacante'}
          </button>
        </form>
      </Modal>

      <GestionCatalogoModal
        tipo="tipos-contrato"
        titulo="tipos de contrato"
        abierto={gestionandoContratos}
        onClose={() => setGestionandoContratos(false)}
        onItemCreado={(id) => actualizar({ tipo_contrato_id: id })}
      />

      {/* ----------------------------------------------------------- Vista previa */}
      <Modal
        open={previa !== null}
        onClose={() => setPrevia(null)}
        title="Así se verá el post"
        wide
      >
        {previa && (
          <div className="space-y-4">
            <div className="rounded-xl border border-slate-200 p-4">
              {previa.imagen_url && (
                <img
                  src={previa.imagen_url}
                  alt="Imagen del post"
                  className="mb-3 max-h-64 w-full rounded-lg object-cover"
                />
              )}
              {/* Sin titular aparte: el cuerpo ya empieza por el asunto, y en LinkedIn
                  no hay encabezado separado. Esto es exactamente lo que se publica. */}
              <p className="whitespace-pre-wrap text-sm text-slate-700">{previa.cuerpo}</p>
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
              <span>{previa.caracteres} caracteres</span>
              <span className="capitalize">Visibilidad: {previa.visibilidad}</span>
              {previa.destinatarios_internos.length > 0 && (
                <span>{previa.destinatarios_internos.length} correo(s) interno(s)</span>
              )}
              {previa.programado_para && (
                <span>Programado: {new Date(previa.programado_para).toLocaleString()}</span>
              )}
            </div>

            <button
              type="button"
              onClick={() => {
                navigator.clipboard?.writeText(previa.cuerpo)
                toast.success('Texto del post copiado')
              }}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              <Send size={15} /> Copiar el texto para compartirlo
            </button>
          </div>
        )}
      </Modal>
    </div>
  )
}
