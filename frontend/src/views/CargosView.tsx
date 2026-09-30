import { useEffect, useState } from 'react'
import { Plus, Trash2, ListChecks, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardBody } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'
import type { TipoRespuesta } from '@/types'

const TIPO_LABELS: Record<TipoRespuesta, string> = {
  multiple: 'Selección múltiple',
  unica: 'Opción única',
  texto: 'Texto libre',
  numero: 'Numérico',
  booleano: 'Sí / No',
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function CargosView() {
  const { cargos, preguntasPorCargo, fetchCargos, createCargo, toggleCargoActivo, fetchPreguntas, addPregunta, removePregunta } =
    useDataStore()
  const [loading, setLoading] = useState(true)
  const [showNewCargo, setShowNewCargo] = useState(false)
  const [preguntasCargoId, setPreguntasCargoId] = useState<number | null>(null)

  const [form, setForm] = useState({ nombre: '', departamento: '', descripcion: '' })
  const [preguntaForm, setPreguntaForm] = useState({ pregunta: '', tipo_respuesta: 'texto' as TipoRespuesta, es_eliminatoria: false })

  useEffect(() => {
    fetchCargos()
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchCargos])

  async function handleCreateCargo(e: React.FormEvent) {
    e.preventDefault()
    if (!form.nombre.trim()) return
    try {
      await createCargo(form)
      toast.success('Cargo creado correctamente')
      setForm({ nombre: '', departamento: '', descripcion: '' })
      setShowNewCargo(false)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleOpenPreguntas(cargoId: number) {
    setPreguntasCargoId(cargoId)
    try {
      await fetchPreguntas(cargoId)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleAddPregunta(e: React.FormEvent) {
    e.preventDefault()
    if (!preguntasCargoId || !preguntaForm.pregunta.trim()) return
    try {
      await addPregunta(preguntasCargoId, preguntaForm)
      toast.success('Pregunta filtro agregada')
      setPreguntaForm({ pregunta: '', tipo_respuesta: 'texto', es_eliminatoria: false })
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleToggleActivo(id: number) {
    try {
      await toggleCargoActivo(id)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleRemovePregunta(preguntaId: number) {
    if (!preguntasCargoId) return
    try {
      await removePregunta(preguntasCargoId, preguntaId)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const cargoActivo = cargos.find((c) => c.id === preguntasCargoId)
  const preguntasDelCargo = preguntasCargoId ? preguntasPorCargo[preguntasCargoId] ?? [] : []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Cargos</h1>
          <p className="text-sm text-slate-500">Catálogo de cargos y preguntas filtro asociadas</p>
        </div>
        <button
          onClick={() => setShowNewCargo(true)}
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
            <Card key={cargo.id} className="flex flex-col justify-between p-4">
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium text-slate-900">{cargo.nombre}</h3>
                  <Badge tone={cargo.activo ? 'green' : 'slate'}>{cargo.activo ? 'Activo' : 'Inactivo'}</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">{cargo.departamento}</p>
                <p className="mt-2 text-sm text-slate-600">{cargo.descripcion}</p>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => handleOpenPreguntas(cargo.id)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  <ListChecks size={14} /> Preguntas
                </button>
                <button
                  onClick={() => handleToggleActivo(cargo.id)}
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  {cargo.activo ? 'Desactivar' : 'Activar'}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showNewCargo} onClose={() => setShowNewCargo(false)} title="Nuevo Cargo">
        <form onSubmit={handleCreateCargo} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Nombre del cargo</label>
            <input
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="Ej. Desarrollador Frontend"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Departamento</label>
            <input
              required
              value={form.departamento}
              onChange={(e) => setForm({ ...form, departamento: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="Ej. Tecnología"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Descripción</label>
            <textarea
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <button type="submit" className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700">
            Crear Cargo
          </button>
        </form>
      </Modal>

      <Modal open={preguntasCargoId !== null} onClose={() => setPreguntasCargoId(null)} title={`Preguntas filtro — ${cargoActivo?.nombre ?? ''}`} wide>
        <div className="space-y-4">
          <div className="space-y-2">
            {preguntasDelCargo.length === 0 && <p className="text-sm text-slate-400">Aún no hay preguntas para este cargo.</p>}
            {preguntasDelCargo.map((p) => (
              <div key={p.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 p-3">
                <div>
                  <p className="text-sm font-medium text-slate-800">{p.pregunta}</p>
                  <div className="mt-1 flex gap-2">
                    <Badge tone="blue">{TIPO_LABELS[p.tipo_respuesta]}</Badge>
                    {p.es_eliminatoria && <Badge tone="red">Eliminatoria</Badge>}
                  </div>
                </div>
                <button onClick={() => handleRemovePregunta(p.id)} className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600">
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <form onSubmit={handleAddPregunta} className="space-y-3 border-t border-slate-100 pt-4">
            <input
              required
              value={preguntaForm.pregunta}
              onChange={(e) => setPreguntaForm({ ...preguntaForm, pregunta: e.target.value })}
              placeholder="Escribe la pregunta filtro"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={preguntaForm.tipo_respuesta}
                onChange={(e) => setPreguntaForm({ ...preguntaForm, tipo_respuesta: e.target.value as TipoRespuesta })}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {Object.entries(TIPO_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={preguntaForm.es_eliminatoria}
                  onChange={(e) => setPreguntaForm({ ...preguntaForm, es_eliminatoria: e.target.checked })}
                />
                Eliminatoria (knockout)
              </label>
              <button type="submit" className="ml-auto flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
                <Plus size={15} /> Agregar
              </button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  )
}
