import { useEffect, useState } from 'react'
import { Plus, Trash2, Loader2, Settings, Users, Star } from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { GestionCatalogoModal } from '@/components/catalogo/GestionCatalogoModal'
import { SelectorCompetencias } from '@/components/catalogo/SelectorCompetencias'
import {
  SelectorMultipleCatalogo,
  type FilaDeCatalogo,
} from '@/components/catalogo/SelectorMultipleCatalogo'
import { BarraExperiencia } from '@/components/catalogo/BarraExperiencia'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'
import {
  EXPERIENCIA_TRAMOS,
  type Cargo,
  type CatalogoItem,
  type CatalogoTipo,
  type CompetenciaDelCargo,
  type EstadoEducacion,
  type ExperienciaRequerida,
} from '@/types'

const CATALOGO_TITULOS: Record<CatalogoTipo, string> = {
  'nombres-cargo': 'nombres de cargo',
  clasificaciones: 'clasificaciones',
  'niveles-educacion': 'niveles de educación',
  titulos: 'títulos',
  'areas-academicas': 'áreas académicas',
}

/** Las actividades se reordenan al marcar favoritas, así que cada fila necesita una clave
 *  estable: con el índice, React reutilizaría el cuadro de texto equivocado. */
interface ActividadForm {
  id: string
  texto: string
  favorita: boolean
}

function actividadNueva(): ActividadForm {
  return { id: crypto.randomUUID(), texto: '', favorita: false }
}

/** Vuelca un cargo existente al formulario. Las actividades reciben su `id` local. */
function formDesdeCargo(cargo: Cargo) {
  return {
    nombre_id: cargo.nombre_id as number | null,
    tiene_personal_a_cargo: cargo.tiene_personal_a_cargo,
    clasificacion_id: cargo.clasificacion_id,
    mision: cargo.mision ?? '',
    actividades:
      cargo.actividades.length > 0
        ? cargo.actividades.map((a) => ({ id: crypto.randomUUID(), texto: a.texto, favorita: a.favorita }))
        : [actividadNueva()],
    niveles_educacion:
      cargo.niveles_educacion.length > 0
        ? cargo.niveles_educacion.map((n) => ({ catalogo_id: n.nivel_id, estado: n.estado }))
        : [filaVacia(true)],
    titulos: cargo.titulos.length > 0 ? cargo.titulos.map((t) => ({ catalogo_id: t.id })) : [filaVacia()],
    areas_academicas:
      cargo.areas_academicas.length > 0
        ? cargo.areas_academicas.map((a) => ({ catalogo_id: a.id }))
        : [filaVacia()],
    experiencia_requerida: cargo.experiencia_requerida,
    experiencia_empresas_similares: cargo.experiencia_empresas_similares,
    experiencia_cargos_similares: cargo.experiencia_cargos_similares,
    experiencia_interna_otros_cargos: cargo.experiencia_interna_otros_cargos,
    competencias: cargo.competencias,
  }
}

/** Fila vacía del selector múltiple; con estado solo para el nivel de educación. */
function filaVacia(conEstado = false): FilaDeCatalogo {
  return { catalogo_id: null, ...(conEstado ? { estado: 'completa' as EstadoEducacion } : {}) }
}

const FORM_VACIO = {
  nombre_id: null as number | null,
  tiene_personal_a_cargo: false,
  clasificacion_id: null as number | null,
  mision: '',
  actividades: [actividadNueva()] as ActividadForm[],
  niveles_educacion: [filaVacia(true)] as FilaDeCatalogo[],
  titulos: [filaVacia()] as FilaDeCatalogo[],
  areas_academicas: [filaVacia()] as FilaDeCatalogo[],
  experiencia_requerida: null as ExperienciaRequerida | null,
  experiencia_empresas_similares: false,
  experiencia_cargos_similares: false,
  experiencia_interna_otros_cargos: false,
  competencias: [] as CompetenciaDelCargo[],
}

/** Las tres exigencias sueltas que acompañan al tramo de años (sección 7). */
const EXIGENCIAS_DE_EXPERIENCIA = [
  { campo: 'experiencia_empresas_similares', etiqueta: 'Experiencia en empresas similares' },
  { campo: 'experiencia_cargos_similares', etiqueta: 'Experiencia en cargos similares' },
  { campo: 'experiencia_interna_otros_cargos', etiqueta: 'Experiencia interna en otros cargos' },
] as const

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/** Cabecera numerada de cada bloque del formulario. */
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

/** Selector alimentado por un catálogo, con el engranaje que lo gestiona al lado. */
function SelectorDeCatalogo({
  label,
  requerido,
  valor,
  onChange,
  items,
  onGestionar,
}: {
  label: string
  requerido?: boolean
  valor: number | null
  onChange: (id: number | null) => void
  items: CatalogoItem[]
  onGestionar: () => void
}) {
  // Un elemento desactivado se sigue mostrando si es el que está seleccionado,
  // para no vaciar el campo en silencio.
  const visibles = items.filter((i) => i.activo || i.id === valor)

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label} {requerido && <span className="text-red-500">*</span>}
      </label>
      <div className="flex gap-2">
        <select
          required={requerido}
          value={valor ?? ''}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">Selecciona...</option>
          {visibles.map((i) => (
            <option key={i.id} value={i.id}>
              {i.nombre}
              {!i.activo ? ' (inactivo)' : ''}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={onGestionar}
          title={`Gestionar ${label.toLowerCase()}`}
          className="shrink-0 rounded-lg border border-slate-300 px-3 text-slate-500 transition-colors hover:bg-slate-50 hover:text-brand-600"
        >
          <Settings size={16} />
        </button>
      </div>
      {visibles.length === 0 && (
        <p className="mt-1 text-xs text-amber-600">
          No hay opciones todavía: usa el engranaje para crear la primera.
        </p>
      )}
    </div>
  )
}

export function CargosView() {
  const { cargos, catalogos, fetchCargos, fetchCatalogo, createCargo, updateCargo, toggleCargoActivo } =
    useDataStore()

  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [showNewCargo, setShowNewCargo] = useState(false)
  /** Cargo que se está editando; `null` cuando el modal crea uno nuevo. */
  const [cargoEnEdicion, setCargoEnEdicion] = useState<Cargo | null>(null)
  const [gestionando, setGestionando] = useState<CatalogoTipo | null>(null)
  /** Cargo cuyo estado se va a cambiar, a la espera de confirmación. */
  const [cargoAConfirmar, setCargoAConfirmar] = useState<Cargo | null>(null)
  const [cambiandoEstado, setCambiandoEstado] = useState(false)

  const [form, setForm] = useState(FORM_VACIO)

  useEffect(() => {
    Promise.all([
      fetchCargos(),
      fetchCatalogo('nombres-cargo'),
      fetchCatalogo('clasificaciones'),
      fetchCatalogo('niveles-educacion'),
      fetchCatalogo('titulos'),
      fetchCatalogo('areas-academicas'),
    ])
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchCargos, fetchCatalogo])

  async function handleCreateCargo(e: React.FormEvent) {
    e.preventDefault()
    if (!form.nombre_id) {
      toast.error('Elige el nombre del cargo')
      return
    }
    setGuardando(true)
    const datos = {
      nombre_id: form.nombre_id,
      tiene_personal_a_cargo: form.tiene_personal_a_cargo,
      clasificacion_id: form.clasificacion_id,
      mision: form.mision.trim() || null,
      // El `id` local no viaja: solo sirve para que React identifique cada fila.
      actividades: form.actividades.map(({ texto, favorita }) => ({ texto, favorita })),
      // Las filas sin elegir no viajan: el formulario siempre muestra una vacía al final.
      niveles_educacion: form.niveles_educacion
        .filter((f) => f.catalogo_id !== null)
        .map((f) => ({ nivel_id: f.catalogo_id as number, estado: f.estado ?? 'completa' })),
      titulos_ids: form.titulos.filter((f) => f.catalogo_id !== null).map((f) => f.catalogo_id as number),
      areas_academicas_ids: form.areas_academicas
        .filter((f) => f.catalogo_id !== null)
        .map((f) => f.catalogo_id as number),
      experiencia_requerida: form.experiencia_requerida,
      experiencia_empresas_similares: form.experiencia_empresas_similares,
      experiencia_cargos_similares: form.experiencia_cargos_similares,
      experiencia_interna_otros_cargos: form.experiencia_interna_otros_cargos,
      competencias: form.competencias.map(({ competencia_id, requerido, deseado }) => ({
        competencia_id,
        requerido,
        deseado,
      })),
    }
    try {
      if (cargoEnEdicion) {
        await updateCargo(cargoEnEdicion.id, datos)
        toast.success('Cargo actualizado')
      } else {
        await createCargo(datos)
        toast.success('Cargo creado correctamente')
      }
      setForm(FORM_VACIO)
      setCargoEnEdicion(null)
      setShowNewCargo(false)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  function cambiarActividad(id: string, texto: string) {
    setForm((f) => ({
      ...f,
      actividades: f.actividades.map((a) => (a.id === id ? { ...a, texto } : a)),
    }))
  }

  /** Marcar como favorita sube la actividad al principio; desmarcarla la devuelve abajo. */
  function alternarFavorita(id: string) {
    setForm((f) => {
      const cambiadas = f.actividades.map((a) => (a.id === id ? { ...a, favorita: !a.favorita } : a))
      // `sort` de JavaScript es estable: dentro de cada grupo se conserva el orden actual.
      return { ...f, actividades: [...cambiadas].sort((a, b) => Number(b.favorita) - Number(a.favorita)) }
    })
  }

  function agregarActividad() {
    setForm((f) => ({ ...f, actividades: [...f.actividades, actividadNueva()] }))
  }

  function quitarActividad(id: string) {
    setForm((f) => {
      const restantes = f.actividades.filter((a) => a.id !== id)
      return { ...f, actividades: restantes.length > 0 ? restantes : [actividadNueva()] }
    })
  }

  function abrirNuevo() {
    setCargoEnEdicion(null)
    setForm(FORM_VACIO)
    setShowNewCargo(true)
  }

  function abrirEdicion(cargo: Cargo) {
    setCargoEnEdicion(cargo)
    setForm(formDesdeCargo(cargo))
    setShowNewCargo(true)
  }

  async function confirmarCambioDeEstado() {
    if (!cargoAConfirmar) return
    setCambiandoEstado(true)
    try {
      await toggleCargoActivo(cargoAConfirmar.id)
      toast.success(cargoAConfirmar.activo ? 'Cargo desactivado' : 'Cargo activado')
      setCargoAConfirmar(null)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setCambiandoEstado(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Cargos</h1>
          <p className="text-sm text-slate-500">
            Descriptivos de puesto. Pulsa el estado de un cargo para activarlo o desactivarlo.
          </p>
        </div>
        <button
          onClick={abrirNuevo}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={16} /> Nuevo Cargo
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cargos.map((cargo) => (
            <Card
              key={cargo.id}
              role="button"
              tabIndex={0}
              onClick={() => abrirEdicion(cargo)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  abrirEdicion(cargo)
                }
              }}
              title="Abrir para ver o modificar este cargo"
              className="flex cursor-pointer flex-col justify-between p-4 transition-shadow hover:border-brand-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-brand-400"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium text-slate-900">{cargo.nombre}</h3>
                  {/* El estado es el interruptor: se pulsa y se confirma. `stopPropagation`
                      evita que el clic abra además el modal de edición de la tarjeta. */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      setCargoAConfirmar(cargo)
                    }}
                    title={cargo.activo ? 'Pulsa para desactivar este cargo' : 'Pulsa para activar este cargo'}
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                      cargo.activo
                        ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {cargo.activo ? 'Activo' : 'Inactivo'}
                  </button>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                  {cargo.clasificacion && <Badge tone="slate">{cargo.clasificacion}</Badge>}
                  {cargo.tiene_personal_a_cargo && (
                    <Badge tone="purple">
                      <Users size={11} className="mr-1 inline" />
                      Personal a cargo
                    </Badge>
                  )}
                </div>
                {cargo.mision && <p className="mt-2 line-clamp-3 text-sm text-slate-600">{cargo.mision}</p>}
                <p className="mt-2 text-xs text-slate-400">
                  {cargo.actividades.length} actividad{cargo.actividades.length === 1 ? '' : 'es'}
                  {cargo.competencias.length > 0 && ` · ${cargo.competencias.length} competencias`}
                  {cargo.experiencia_requerida &&
                    ` · ${EXPERIENCIA_TRAMOS.find((t) => t.valor === cargo.experiencia_requerida)?.etiqueta}`}
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* ---------- Nuevo cargo ---------- */}
      <Modal
        open={showNewCargo}
        onClose={() => {
          setShowNewCargo(false)
          setCargoEnEdicion(null)
        }}
        title={cargoEnEdicion ? `Editar: ${cargoEnEdicion.nombre}` : 'Nuevo Cargo'}
        wide
        confirmarCierre="Se perderá lo que hayas escrito en las siete secciones."
      >
        <form onSubmit={handleCreateCargo} className="space-y-6">
          <Seccion numero={1} titulo="Identificación del puesto">
            <SelectorDeCatalogo
              label="Nombre del cargo"
              requerido
              valor={form.nombre_id}
              onChange={(id) => setForm({ ...form, nombre_id: id })}
              items={catalogos['nombres-cargo']}
              onGestionar={() => setGestionando('nombres-cargo')}
            />

            <label className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-slate-200 px-3 py-2.5">
              <input
                type="checkbox"
                checked={form.tiene_personal_a_cargo}
                onChange={(e) => setForm({ ...form, tiene_personal_a_cargo: e.target.checked })}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              <span className="text-sm text-slate-700">¿Tiene personal a cargo?</span>
            </label>

            <SelectorDeCatalogo
              label="Clasificación"
              valor={form.clasificacion_id}
              onChange={(id) => setForm({ ...form, clasificacion_id: id })}
              items={catalogos.clasificaciones}
              onGestionar={() => setGestionando('clasificaciones')}
            />
          </Seccion>

          <Seccion numero={2} titulo="Misión del cargo">
            <textarea
              value={form.mision}
              onChange={(e) => setForm({ ...form, mision: e.target.value })}
              rows={5}
              placeholder="¿Para qué existe este puesto? Describe en pocas líneas su propósito dentro de la organización."
              className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </Seccion>

          <Seccion numero={3} titulo="Actividades del cargo">
            <div className="overflow-hidden rounded-lg border border-slate-300">
              {form.actividades.map((actividad, i) => (
                <div
                  key={actividad.id}
                  className={`flex items-stretch border-b border-slate-200 last:border-b-0 ${
                    actividad.favorita ? 'bg-amber-50/60' : ''
                  }`}
                >
                  <span className="flex w-9 shrink-0 justify-center bg-slate-50 pt-2.5 text-xs font-semibold text-slate-400">
                    {i + 1}
                  </span>
                  <textarea
                    value={actividad.texto}
                    onChange={(e) => cambiarActividad(actividad.id, e.target.value)}
                    rows={2}
                    placeholder="Describe la actividad..."
                    className="min-w-0 flex-1 resize-y border-0 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-inset focus:ring-brand-500"
                  />
                  <button
                    type="button"
                    onClick={() => alternarFavorita(actividad.id)}
                    title={actividad.favorita ? 'Quitar de destacadas' : 'Destacar: sube al principio'}
                    aria-pressed={actividad.favorita}
                    className={`shrink-0 px-2.5 transition-colors ${
                      actividad.favorita
                        ? 'text-amber-500 hover:text-amber-600'
                        : 'text-slate-300 hover:bg-amber-50 hover:text-amber-500'
                    }`}
                  >
                    <Star size={15} fill={actividad.favorita ? 'currentColor' : 'none'} />
                  </button>
                  <button
                    type="button"
                    onClick={() => quitarActividad(actividad.id)}
                    title="Quitar actividad"
                    className="shrink-0 px-3 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={agregarActividad}
                className="flex w-full items-center justify-center gap-1.5 border-t border-dashed border-slate-300 bg-slate-50 py-2.5 text-xs font-medium text-brand-600 transition-colors hover:bg-brand-50"
              >
                <Plus size={14} /> Agregar actividad
              </button>
            </div>
            <p className="text-xs text-slate-400">
              La estrella destaca una actividad y la sube al principio. Las vacías no se guardan:
              puedes dejar filas de sobra sin problema.
            </p>
          </Seccion>

          <Seccion numero={4} titulo="Educación formal requerida">
            <SelectorMultipleCatalogo
              label="Nivel de educación formal"
              filas={form.niveles_educacion}
              onChange={(filas) => setForm((f) => ({ ...f, niveles_educacion: filas }))}
              items={catalogos['niveles-educacion']}
              onGestionar={() => setGestionando('niveles-educacion')}
              conEstado
              textoAgregar="Agregar otro nivel"
            />

            <SelectorMultipleCatalogo
              label="Título requerido"
              filas={form.titulos}
              onChange={(filas) => setForm((f) => ({ ...f, titulos: filas }))}
              items={catalogos.titulos}
              onGestionar={() => setGestionando('titulos')}
              textoAgregar="Agregar otro título"
            />

            <SelectorMultipleCatalogo
              label="Área académica de especialización"
              filas={form.areas_academicas}
              onChange={(filas) => setForm((f) => ({ ...f, areas_academicas: filas }))}
              items={catalogos['areas-academicas']}
              onGestionar={() => setGestionando('areas-academicas')}
              textoAgregar="Agregar otra área"
            />
          </Seccion>

          <Seccion numero={5} titulo="Formación">
            <SelectorCompetencias
              tipo="academico"
              etiqueta="Conocimientos académicos"
              placeholder="Ej. Contabilidad de costos, SQL, Normas NIIF..."
              seleccionadas={form.competencias.filter((c) => c.tipo === 'academico')}
              onChange={(academicos) =>
                setForm((f) => ({
                  ...f,
                  competencias: [...f.competencias.filter((c) => c.tipo !== 'academico'), ...academicos],
                }))
              }
            />
          </Seccion>

          <Seccion numero={6} titulo="Habilidades blandas">
            <SelectorCompetencias
              tipo="blanda"
              etiqueta="Destrezas y habilidades"
              placeholder="Ej. Trabajo en equipo, Comunicación efectiva..."
              seleccionadas={form.competencias.filter((c) => c.tipo === 'blanda')}
              onChange={(blandas) =>
                setForm((f) => ({
                  ...f,
                  competencias: [...f.competencias.filter((c) => c.tipo !== 'blanda'), ...blandas],
                }))
              }
            />
          </Seccion>

          <Seccion numero={7} titulo="Experiencia requerida">
            <BarraExperiencia
              valor={form.experiencia_requerida}
              onChange={(valor) => setForm((f) => ({ ...f, experiencia_requerida: valor }))}
            />

            <div className="overflow-hidden rounded-lg border border-slate-200">
              {EXIGENCIAS_DE_EXPERIENCIA.map(({ campo, etiqueta }) => (
                <label
                  key={campo}
                  className="flex cursor-pointer items-center gap-2.5 border-b border-slate-100 px-3 py-2.5 last:border-b-0 hover:bg-slate-50"
                >
                  <input
                    type="checkbox"
                    checked={form[campo]}
                    onChange={(e) => setForm((f) => ({ ...f, [campo]: e.target.checked }))}
                    className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className="text-sm text-slate-700">{etiqueta}</span>
                </label>
              ))}
            </div>
          </Seccion>

          <button
            type="submit"
            disabled={guardando}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {guardando && <Loader2 size={15} className="animate-spin" />}
            {cargoEnEdicion ? 'Guardar cambios' : 'Crear Cargo'}
          </button>
        </form>
      </Modal>

      {/* Hermano del modal anterior, no hijo: así se dibuja encima sin pelear por el z-index. */}
      <GestionCatalogoModal
        tipo={gestionando ?? 'nombres-cargo'}
        titulo={gestionando ? CATALOGO_TITULOS[gestionando] : ''}
        abierto={gestionando !== null}
        onClose={() => setGestionando(null)}
        onItemCreado={(id) => {
          // Si el campo estaba vacío, se selecciona lo recién creado.
          if (gestionando === 'nombres-cargo' && !form.nombre_id) setForm((f) => ({ ...f, nombre_id: id }))
          if (gestionando === 'clasificaciones' && !form.clasificacion_id)
            setForm((f) => ({ ...f, clasificacion_id: id }))
        }}
      />

      {/* ---------- Confirmar activar / desactivar ---------- */}
      <Modal
        open={cargoAConfirmar !== null}
        onClose={() => setCargoAConfirmar(null)}
        title={cargoAConfirmar?.activo ? 'Desactivar cargo' : 'Activar cargo'}
      >
        <div className="space-y-5">
          <p className="text-sm text-slate-600">
            {cargoAConfirmar?.activo ? (
              <>
                ¿Seguro que quieres desactivar <strong>{cargoAConfirmar?.nombre}</strong>? Dejará de
                ofrecerse al crear vacantes nuevas. Las vacantes que ya lo usan no se tocan.
              </>
            ) : (
              <>
                ¿Seguro que quieres activar <strong>{cargoAConfirmar?.nombre}</strong>? Volverá a
                estar disponible al crear vacantes.
              </>
            )}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setCargoAConfirmar(null)}
              className="flex-1 rounded-lg border border-slate-300 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmarCambioDeEstado}
              disabled={cambiandoEstado}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-60 ${
                cargoAConfirmar?.activo
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-brand-600 hover:bg-brand-700'
              }`}
            >
              {cambiandoEstado && <Loader2 size={15} className="animate-spin" />}
              Sí
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
