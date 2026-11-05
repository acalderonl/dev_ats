import { useEffect, useMemo, useState } from 'react'
import {
  Calendar,
  Clock,
  Copy,
  DollarSign,
  Eye,
  FileText,
  Image as ImageIcon,
  Linkedin,
  Loader2,
  Mail,
  MessageCircle,
  Plus,
  RefreshCw,
  Send,
  Settings2,
  Trash2,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { SimulacionDeRedSocial } from '@/components/common/SimulacionDeRedSocial'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { GestionCatalogoModal } from '@/components/catalogo/GestionCatalogoModal'
import { CamposPersonalizados } from '@/components/vacantes/CamposPersonalizados'
import { SelectorDeHorario } from '@/components/vacantes/SelectorDeHorario'
import { useDataStore } from '@/store/dataStore'
import { useAuthStore } from '@/store/authStore'
import { configuracionService, convocatoriasService, vacantesService } from '@/services/vacantesService'
import { ApiError } from '@/lib/apiClient'
import type {
  CampoPersonalizado,
  EstadoVacante,
  Jornada,
  ParaCompartirEnLinkedIn,
  Vacante,
  VisibilidadVacante,
  VistaPreviaDelPost,
  Convocatoria,
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

/**
 * La convocatoria sobre la que se actúa desde la tarjeta: la más reciente.
 *
 * Una vacante siempre tiene al menos una (nace con ella y la migración se la creó a
 * las existentes), así que llegar aquí sin ninguna es un dato roto, no un caso de uso.
 */
function cicloDe(v: Vacante): Convocatoria {
  if (!v.convocatoria_actual) throw new Error(`La vacante «${v.titulo}» no tiene ninguna convocatoria`)
  return v.convocatoria_actual
}

function formDesdeVacante(v: Vacante): FormularioDeVacante {
  // El formulario mezcla condiciones (de la vacante) y ciclo (de la convocatoria actual)
  // porque así lo arma la persona; al guardar se separan otra vez.
  const c = cicloDe(v)
  return {
    cargo_id: v.cargo_id,
    descripcion: v.descripcion,
    fecha_limite: aInputLocal(c.fecha_limite),
    remuneracion: v.remuneracion ?? '',
    jornada_horas: v.jornada_horas ?? '',
    hora_entrada: v.hora_entrada?.slice(0, 5) ?? '',
    hora_salida: v.hora_salida?.slice(0, 5) ?? '',
    tipo_contrato_id: v.tipo_contrato_id,
    campos_personalizados: v.campos_personalizados ?? [],
    asunto: c.asunto ?? '',
    post_cuerpo: c.post_cuerpo ?? '',
    post_imagen_url: c.post_imagen_url,
    post_programado_para: aInputLocal(c.post_programado_para),
    estado: c.estado,
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
  // Deliberadamente distinto de "publicado": al abrir el compositor entregamos el
  // contenido, pero quien pulsa Publicar es la persona y no podemos comprobarlo.
  compartido: 'Enviado a LinkedIn',
  publicado: 'Post publicado',
  error: 'Post con error',
}

const PUNTO_DEL_POST: Record<string, string> = {
  borrador: 'bg-slate-300',
  programado: 'bg-amber-400',
  compartido: 'bg-sky-500',
  publicado: 'bg-emerald-500',
  error: 'bg-red-500',
}

/** Una condición del puesto: icono y texto, en una etiqueta que no se parte. */
function Dato({ icono: Icono, children }: { icono: typeof Clock; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-600 ring-1 ring-inset ring-slate-200">
      <Icono size={12} className="shrink-0 text-slate-400" />
      {children}
    </span>
  )
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
    cambiarEstadoConvocatoria,
    abrirConvocatoria,
    actualizarConvocatoria,
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
  /** Lo que se mandó a LinkedIn, para poder reabrir el texto si el pegado falló. */
  const [compartido, setCompartido] = useState<ParaCompartirEnLinkedIn | null>(null)
  const [publicandoId, setPublicandoId] = useState<string | null>(null)
  // Volver a convocar: solo pide la nueva fecha de cierre; el post se hereda del anterior.
  const [convocando, setConvocando] = useState<Vacante | null>(null)
  const [nuevaFechaLimite, setNuevaFechaLimite] = useState('')
  const [abriendoConvocatoria, setAbriendoConvocatoria] = useState(false)

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

  /** La parte del formulario que es del ciclo: va a la convocatoria. */
  function cicloDelFormulario() {
    return {
      fecha_limite: new Date(form.fecha_limite).toISOString(),
      estado: form.estado,
      asunto: form.asunto || null,
      post_cuerpo: form.post_cuerpo || null,
      post_imagen_url: form.post_imagen_url,
      post_programado_para: form.post_programado_para
        ? new Date(form.post_programado_para).toISOString()
        : null,
    }
  }

  /**
   * Lo que el formulario manda al servidor: las condiciones, con el ciclo anidado
   * como `primera_convocatoria`. Al crear, el servidor usa las dos partes; al editar
   * ignora la anidada y el ciclo se manda aparte a la convocatoria actual.
   */
  function payloadDelFormulario() {
    return {
      cargo_id: Number(form.cargo_id),
      descripcion: form.descripcion,
      remuneracion: form.remuneracion || null,
      jornada_horas: form.jornada_horas || null,
      hora_entrada: form.hora_entrada || null,
      hora_salida: form.hora_salida || null,
      tipo_contrato_id: form.tipo_contrato_id,
      campos_personalizados: form.campos_personalizados.filter((c) => c.etiqueta.trim()),
      visibilidad: form.visibilidad,
      destinatarios_internos: correosInternos,
      primera_convocatoria: cicloDelFormulario(),
    }
  }

  /**
   * La simulación con lo que hay escrito ahora, sin guardar.
   *
   * El texto lo arma el servidor con las mismas piezas que publica: así lo que se ve
   * aquí es lo que va a salir, no una reconstrucción parecida hecha en la pantalla.
   */
  async function verSimulacionDelFormulario() {
    if (!form.cargo_id) return toast.error('Elige primero el cargo: de él sale el título del post')
    if (!form.fecha_limite) return toast.error('Falta la fecha límite: sale en el post')
    try {
      setPrevia(await vacantesService.vistaPreviaSinGuardar(payloadDelFormulario()))
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault()
    if (!form.cargo_id) return toast.error('Elige el cargo de la vacante')
    if (!form.fecha_limite) return toast.error('Falta la fecha límite')
    if (necesitaCorreos && correosInternos.length === 0) {
      return toast.error('Una vacante interna o mixta necesita al menos un correo destinatario')
    }

    const payload = payloadDelFormulario()

    setGuardando(true)
    try {
      let vacante: Vacante
      if (enEdicion) {
        // Dos llamadas a propósito: las condiciones son de la vacante y el ciclo es
        // de la convocatoria actual. El servidor ignora la parte anidada al editar.
        vacante = await updateVacante(enEdicion.id, payload)
        await actualizarConvocatoria(cicloDe(enEdicion).id, cicloDelFormulario())
      } else {
        vacante = await createVacante(payload)
      }
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
      setPrevia(await convocatoriasService.vistaPrevia(cicloDe(vacante).id))
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  /** Si el post existe de verdad en LinkedIn. Un id simulado no se puede tocar allí. */
  function tienePostEnLinkedIn(vacante: Vacante): boolean {
    return Boolean(vacante.convocatoria_actual?.linkedin_post_id && !vacante.convocatoria_actual.linkedin_post_id.includes('simulado'))
  }

  /** Reescribe el texto del post con lo que dice hoy la vacante. */
  async function actualizarPost(vacante: Vacante) {
    setPublicandoId(vacante.id)
    try {
      const { mensaje } = await convocatoriasService.actualizarPostEnLinkedIn(cicloDe(vacante).id)
      toast.success(mensaje)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  /**
   * Borra el post de LinkedIn.
   *
   * Se pregunta antes: es algo que ya vio gente y que no se deshace. Al borrarlo la
   * vacante vuelve a borrador, porque decir "publicado" de algo que ya no existe
   * sería mentir en la propia pantalla.
   */
  async function quitarDeLinkedIn(vacante: Vacante) {
    const seguro = window.confirm(
      `¿Borrar de LinkedIn el post de «${vacante.titulo}»?\n\n` +
        'Desaparece del muro de quien lo publicó y no se puede deshacer. ' +
        'La vacante vuelve a borrador y podrás volver a publicarla.',
    )
    if (!seguro) return

    setPublicandoId(vacante.id)
    try {
      const { mensaje } = await convocatoriasService.borrarPostEnLinkedIn(cicloDe(vacante).id)
      toast.success(mensaje)
      await fetchVacantes()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  /**
   * Vuelve a convocar la vacante.
   *
   * Solo se pide la nueva fecha de cierre: el asunto, el texto y la imagen se heredan
   * de la convocatoria anterior (lo hace el servidor), que es lo que pidió el dueño:
   * «con los mismos datos que ya se crearon». La anterior se cierra si seguía abierta.
   */
  async function convocarDeNuevo() {
    if (!convocando) return
    if (!nuevaFechaLimite) return toast.error('Falta la fecha de cierre de la nueva convocatoria')
    setAbriendoConvocatoria(true)
    try {
      await abrirConvocatoria(convocando.id, {
        fecha_limite: new Date(nuevaFechaLimite).toISOString(),
        estado: 'abierta',
      })
      toast.success(`Convocatoria ${cicloDe(convocando).numero + 1} abierta para «${convocando.titulo}»`)
      setConvocando(null)
      setNuevaFechaLimite('')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setAbriendoConvocatoria(false)
    }
  }

  async function publicar(vacante: Vacante) {
    setPublicandoId(vacante.id)
    try {
      const { simulado, mensaje } = await publicarEnLinkedIn(cicloDe(vacante).id)
      if (simulado) toast.warning(mensaje)
      else toast.success(mensaje)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  /**
   * Lleva la vacante a LinkedIn sin API: copia el texto y abre el compositor.
   *
   * La ventana se abre **antes** de esperar al servidor. Los navegadores solo dejan
   * abrir pestañas como consecuencia directa de un clic; si se abriera después del
   * `await`, el bloqueador de ventanas emergentes la pararía.
   */
  async function compartirEnLinkedIn(vacante: Vacante) {
    const pestana = window.open('', '_blank')
    setPublicandoId(vacante.id)
    try {
      const datos = await convocatoriasService.compartirEnLinkedIn(cicloDe(vacante).id)
      // El portapapeles también quiere el gesto del usuario cerca; va antes de nada
      // más por si falla, para poder avisar.
      let copiado = true
      try {
        await navigator.clipboard.writeText(datos.texto)
      } catch {
        copiado = false
      }

      if (pestana) pestana.location.href = datos.url_del_compositor
      else window.open(datos.url_del_compositor, '_blank')

      setCompartido(datos)
      await fetchVacantes()
      if (copiado) toast.success('Texto copiado. Pégalo en LinkedIn y publica.')
      else toast.warning('No se pudo copiar solo: cópialo desde la ventana que se abrió.')
    } catch (err) {
      pestana?.close()
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  async function enviar(vacante: Vacante) {
    setPublicandoId(vacante.id)
    try {
      toast.success(await enviarInterno(cicloDe(vacante).id))
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setPublicandoId(null)
    }
  }

  function copiarEnlace(vacante: Vacante) {
    const url = cicloDe(vacante).url_publica ?? `${window.location.origin}/postular/${cicloDe(vacante).slug}`
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
        <Card className="p-10">
          <p className="text-center text-sm text-slate-500">
            Todavía no hay vacantes. Crea una desde un cargo existente.
          </p>
        </Card>
      )}

      <div className="grid items-stretch gap-5 md:grid-cols-2">
        {vacantes.map((vacante) => {
          const postulantes = postulaciones.filter((p) => p.vacante_id === vacante.id).length
          return (
            <Card
              key={vacante.id}
              className="flex h-full flex-col overflow-hidden transition-shadow hover:border-brand-300 hover:shadow-md"
            >
              <div
                role="button"
                tabIndex={0}
                onClick={() => abrirEdicion(vacante)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    abrirEdicion(vacante)
                  }
                }}
                className="flex-1 cursor-pointer space-y-4 p-5 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-brand-400"
                title="Abrir para ver o modificar esta vacante"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-semibold leading-snug text-slate-900">
                    {vacante.titulo}
                  </h3>
                  <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
                    <Badge tone={TONO_DE_ESTADO[cicloDe(vacante).estado]}>{cicloDe(vacante).estado}</Badge>
                    <Badge tone={vacante.visibilidad === 'publica' ? 'blue' : 'slate'}>
                      {vacante.visibilidad}
                    </Badge>
                  </div>
                </div>

                {vacante.descripcion && (
                  <p className="line-clamp-2 text-sm leading-relaxed text-slate-600">
                    {vacante.descripcion}
                  </p>
                )}

                {/* Las condiciones, como etiquetas: en una fila de texto suelto se leían
                    como una frase rota cuando faltaba alguna. */}
                <div className="flex flex-wrap gap-1.5">
                  {vacante.remuneracion && (
                    <Dato icono={DollarSign}>{Number(vacante.remuneracion).toFixed(2)}</Dato>
                  )}
                  {vacante.hora_entrada && vacante.hora_salida && (
                    <Dato icono={Clock}>
                      {vacante.hora_entrada.slice(0, 5)} – {vacante.hora_salida.slice(0, 5)}
                    </Dato>
                  )}
                  {vacante.tipo_contrato_nombre && (
                    <Dato icono={FileText}>{vacante.tipo_contrato_nombre}</Dato>
                  )}
                  <Dato icono={Users}>
                    {postulantes} {postulantes === 1 ? 'postulante' : 'postulantes'}
                  </Dato>
                </div>

                {/* Qué ronda es y cuánta gente ha entrado por ella. Si hubo más de una,
                    se dice: es el histórico que pidió el dueño para el control. */}
                <p className="text-xs text-slate-500">
                  Convocatoria {cicloDe(vacante).numero}
                  {vacante.convocatorias.length > 1 && ` de ${vacante.convocatorias.length}`}
                  {' · '}
                  {cicloDe(vacante).postulantes === 1 ? '1 postulante' : `${cicloDe(vacante).postulantes} postulantes`}
                  {!vacante.activa && <span className="ml-2 text-red-600">· vacante inactiva</span>}
                </p>
                <div className="flex items-center gap-2 border-t border-slate-100 pt-3 text-xs">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${PUNTO_DEL_POST[cicloDe(vacante).post_estado]}`} />
                  <span className="text-slate-600">{ETIQUETA_DEL_POST[cicloDe(vacante).post_estado]}</span>
                  {cicloDe(vacante).post_programado_para && cicloDe(vacante).post_estado === 'programado' && (
                    <span className="truncate text-slate-400">
                      · {new Date(cicloDe(vacante).post_programado_para!).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
                <button
                  onClick={() => verVistaPrevia(vacante)}
                  className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900"
                >
                  <Eye size={13} /> Vista previa
                </button>
                <button
                  onClick={() => copiarEnlace(vacante)}
                  className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900"
                >
                  <Copy size={13} /> Enlace
                </button>
                {vacante.visibilidad !== 'interna' && (
                  <button
                    onClick={() => compartirEnLinkedIn(vacante)}
                    disabled={publicandoId === vacante.id || cicloDe(vacante).estado !== 'abierta'}
                    title={
                      cicloDe(vacante).estado !== 'abierta'
                        ? 'Solo se comparte una vacante abierta'
                        : 'Copia el texto y abre LinkedIn para publicar'
                    }
                    className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-[#0a66c2] shadow-sm transition-colors hover:border-[#0a66c2] hover:bg-[#0a66c2]/5 disabled:cursor-not-allowed disabled:text-slate-400 disabled:opacity-50 disabled:hover:border-slate-200 disabled:hover:bg-white"
                  >
                    {publicandoId === vacante.id ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Linkedin size={13} />
                    )}
                    LinkedIn
                  </button>
                )}
                {tienePostEnLinkedIn(vacante) && (
                  <>
                    <button
                      onClick={() => actualizarPost(vacante)}
                      disabled={publicandoId === vacante.id}
                      title="Reescribe el texto del post con los datos de hoy. El enlace y la imagen no se pueden cambiar."
                      className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900 disabled:opacity-50"
                    >
                      <RefreshCw size={13} /> Actualizar post
                    </button>
                    <button
                      onClick={() => quitarDeLinkedIn(vacante)}
                      disabled={publicandoId === vacante.id}
                      title="Borra el post de LinkedIn y devuelve la vacante a borrador"
                      className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-red-600 shadow-sm transition-colors hover:border-red-300 hover:bg-red-50 disabled:opacity-50"
                    >
                      <Trash2 size={13} /> Quitar de LinkedIn
                    </button>
                  </>
                )}
                {vacante.visibilidad !== 'publica' && (
                  <button
                    onClick={() => enviar(vacante)}
                    disabled={publicandoId === vacante.id}
                    className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900 disabled:opacity-50"
                  >
                    <Mail size={13} /> Enviar interno
                  </button>
                )}
                <button
                  onClick={() => compartirWhatsApp(cicloDe(vacante).id)}
                  className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900"
                >
                  <MessageCircle size={13} /> WhatsApp
                </button>
                {vacante.activa && (
                  <button
                    onClick={() => {
                      setConvocando(vacante)
                      setNuevaFechaLimite('')
                    }}
                    title="Abre una convocatoria nueva con el mismo post; la actual se cierra si seguía abierta"
                    className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900"
                  >
                    <RefreshCw size={13} /> Nueva convocatoria
                  </button>
                )}
                {cicloDe(vacante).estado !== 'cerrada' && (
                  <button
                    onClick={() => cambiarEstadoConvocatoria(cicloDe(vacante).id, 'cerrada').catch((e) => toast.error(errorMessage(e)))}
                    className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-red-600 shadow-sm transition-colors hover:border-red-300 hover:bg-red-50"
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
          {/* Arriba del todo, para poder mirar cómo va quedando el post sin bajar
              hasta el final ni guardar una vacante a medias. */}
          <button
            type="button"
            onClick={verSimulacionDelFormulario}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-brand-200 bg-brand-50 py-2.5 text-sm font-medium text-brand-700 transition-colors hover:border-brand-300 hover:bg-brand-100"
          >
            <Eye size={15} /> Ver cómo quedará el post
          </button>

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
                    {cicloDe(enEdicion).url_publica ?? `${window.location.origin}/postular/${cicloDe(enEdicion).slug}`}
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
                <div className="overflow-hidden rounded-lg border border-slate-200">
                  <img
                    src={form.post_imagen_url}
                    alt="Imagen del post"
                    className="max-h-56 w-full bg-slate-50 object-contain"
                  />
                  <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-3 py-2">
                    <span className="truncate text-xs text-slate-500">
                      Así se verá en la tarjeta del post
                    </span>
                    <div className="flex shrink-0 gap-3">
                      <label className="cursor-pointer text-xs font-medium text-brand-600 hover:underline">
                        Cambiar
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
                      <button
                        type="button"
                        onClick={() => actualizar({ post_imagen_url: null })}
                        className="flex items-center gap-1 text-xs text-red-600 hover:underline"
                      >
                        <Trash2 size={13} /> Quitar
                      </button>
                    </div>
                  </div>
                  {form.post_imagen_url.toLowerCase().endsWith('.webp') && (
                    <p className="border-t border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                      Es WebP: se guarda bien, pero la red social no acepta ese formato y el post
                      saldría sin imagen. Súbela en JPG o PNG.
                    </p>
                  )}
                </div>
              ) : (
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 py-4 text-sm text-slate-500 hover:border-brand-400 hover:text-brand-600">
                  {subiendoImagen ? <Loader2 size={16} className="animate-spin" /> : <ImageIcon size={16} />}
                  {subiendoImagen ? 'Subiendo...' : 'JPG, PNG o GIF (máx. 5 MB)'}
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

      {/* ----------------------------------------------- Nueva convocatoria */}
      <Modal
        open={convocando !== null}
        onClose={() => setConvocando(null)}
        title={convocando ? `Convocatoria ${cicloDe(convocando).numero + 1}: ${convocando.titulo}` : ''}
      >
        {convocando && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              convocarDeNuevo()
            }}
            className="space-y-4"
          >
            <p className="text-sm text-slate-600">
              Se abre una ronda nueva con el <strong>mismo post</strong> (asunto, texto e imagen) y
              un enlace propio. Las condiciones son las de la vacante.
              {cicloDe(convocando).estado === 'abierta' && (
                <> La convocatoria {cicloDe(convocando).numero}, que sigue abierta, se cierra.</>
              )}
            </p>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Nueva fecha de cierre <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                required
                value={nuevaFechaLimite}
                onChange={(e) => setNuevaFechaLimite(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setConvocando(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={abriendoConvocatoria}
                className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
              >
                {abriendoConvocatoria && <Loader2 size={15} className="animate-spin" />}
                Abrir convocatoria
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* ----------------------------------------------------------- Vista previa */}
      <Modal
        open={previa !== null}
        onClose={() => setPrevia(null)}
        title="Así se verá el post"
        wide
      >
        {previa && (
          <div className="space-y-4">
            <SimulacionDeRedSocial previa={previa} />
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

      {/* ------------------------------------------------ Enviado a LinkedIn */}
      <Modal
        open={compartido !== null}
        onClose={() => setCompartido(null)}
        title="Termina de publicar en LinkedIn"
        wide
      >
        {compartido && (
          <div className="space-y-4">
            <p className="rounded-lg bg-[#0a66c2]/5 p-3 text-sm text-slate-700">
              Se abrió LinkedIn en otra pestaña con la tarjeta de la vacante.{' '}
              <strong>Pega el texto</strong> (ya está en tu portapapeles) y pulsa publicar.
            </p>

            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700">El texto</span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard?.writeText(compartido.texto)
                    toast.success('Copiado otra vez')
                  }}
                  className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline"
                >
                  <Copy size={12} /> Copiar
                </button>
              </div>
              <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-slate-50 p-3 font-sans text-sm text-slate-700">
                {compartido.texto}
              </pre>
            </div>

            <p className="text-xs text-slate-500">{compartido.aviso}</p>

            {/* Honestidad en la pantalla: el sistema entregó el contenido, pero quién
                pulsa Publicar es la persona y eso no se puede comprobar desde aquí. */}
            <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
              La vacante queda marcada como <strong>«Enviado a LinkedIn»</strong>, no como
              publicada: desde aquí no se puede saber si llegaste a pulsar Publicar.
            </p>

            <button
              type="button"
              onClick={() => window.open(compartido.url_del_compositor, '_blank')}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#0a66c2] py-2.5 text-sm font-medium text-white hover:bg-[#004182]"
            >
              <Linkedin size={15} /> Volver a abrir LinkedIn
            </button>
          </div>
        )}
      </Modal>
    </div>
  )
}
