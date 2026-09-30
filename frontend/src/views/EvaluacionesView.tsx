import { useEffect, useMemo, useState } from 'react'
import { Plus, ClipboardCheck, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardBody, CardHeader } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { EmptyState } from '@/components/common/EmptyState'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'
import type { Evaluacion, Postulacion } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

const EVALUABLES: Postulacion['estado_pipeline'][] = ['evaluaciones', 'entrevista', 'contratado', 'descartado']

export function EvaluacionesView() {
  const { postulaciones, evaluacionesPorPostulacion, fetchPostulaciones, fetchEvaluaciones, addEvaluacion } = useDataStore()
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ postulacion_id: '', tipo_evaluacion: 'Entrevista Técnica', puntaje: 80, observaciones: '' })

  const candidatosEvaluables = useMemo(
    () => postulaciones.filter((p) => EVALUABLES.includes(p.estado_pipeline)),
    [postulaciones]
  )

  useEffect(() => {
    fetchPostulaciones()
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchPostulaciones])

  useEffect(() => {
    if (candidatosEvaluables.length === 0) return
    Promise.all(candidatosEvaluables.map((p) => fetchEvaluaciones(p.id))).catch((err) => toast.error(errorMessage(err)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidatosEvaluables.map((p) => p.id).join(',')])

  const evaluacionesConContexto = useMemo(() => {
    const items: { evaluacion: Evaluacion; postulacion: Postulacion }[] = []
    for (const postulacion of candidatosEvaluables) {
      const lista = evaluacionesPorPostulacion[postulacion.id] ?? []
      for (const evaluacion of lista) items.push({ evaluacion, postulacion })
    }
    return items.sort((a, b) => (a.evaluacion.creado_en < b.evaluacion.creado_en ? 1 : -1))
  }, [candidatosEvaluables, evaluacionesPorPostulacion])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.postulacion_id) return
    try {
      await addEvaluacion(form.postulacion_id, {
        tipo_evaluacion: form.tipo_evaluacion,
        puntaje: Number(form.puntaje),
        observaciones: form.observaciones,
      })
      toast.success('Evaluación registrada')
      setForm({ postulacion_id: '', tipo_evaluacion: 'Entrevista Técnica', puntaje: 80, observaciones: '' })
      setShowNew(false)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Evaluaciones</h1>
          <p className="text-sm text-slate-500">Resultados reservados de pruebas, entrevistas y desempeño</p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={16} /> Registrar Evaluación
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : evaluacionesConContexto.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="Sin evaluaciones" description="Registra la primera evaluación de un candidato." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {evaluacionesConContexto.map(({ evaluacion, postulacion }) => (
            <Card key={evaluacion.id}>
              <CardHeader>
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {postulacion.postulante_nombres} {postulacion.postulante_apellidos}
                  </p>
                  <p className="text-xs text-slate-500">{postulacion.vacante_titulo}</p>
                </div>
                {evaluacion.puntaje !== null && (
                  <Badge tone={evaluacion.puntaje >= 70 ? 'green' : evaluacion.puntaje >= 50 ? 'amber' : 'red'}>
                    {evaluacion.puntaje} pts
                  </Badge>
                )}
              </CardHeader>
              <CardBody>
                <p className="text-xs font-semibold uppercase text-slate-400">{evaluacion.tipo_evaluacion}</p>
                <p className="mt-2 text-sm text-slate-600">{evaluacion.observaciones}</p>
                <p className="mt-3 text-xs text-slate-400">{new Date(evaluacion.creado_en).toLocaleDateString('es-EC')}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showNew} onClose={() => setShowNew(false)} title="Registrar Evaluación" wide>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Candidato / Postulación</label>
            <select
              required
              value={form.postulacion_id}
              onChange={(e) => setForm({ ...form, postulacion_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">Selecciona un candidato</option>
              {candidatosEvaluables.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.postulante_nombres} {p.postulante_apellidos} — {p.vacante_titulo}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Tipo de evaluación</label>
              <select
                value={form.tipo_evaluacion}
                onChange={(e) => setForm({ ...form, tipo_evaluacion: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option>Entrevista Técnica</option>
                <option>Prueba Psicométrica</option>
                <option>Evaluación de Desempeño</option>
                <option>Entrevista con Gerencia</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Puntaje (0-100)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={form.puntaje}
                onChange={(e) => setForm({ ...form, puntaje: Number(e.target.value) })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Observaciones confidenciales</label>
            <textarea
              value={form.observaciones}
              onChange={(e) => setForm({ ...form, observaciones: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <button type="submit" className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700">
            Guardar Evaluación
          </button>
        </form>
      </Modal>
    </div>
  )
}
