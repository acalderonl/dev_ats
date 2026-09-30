import { useEffect, useMemo, useState } from 'react'
import { DragDropContext, Droppable, type DropResult } from '@hello-pangea/dnd'
import { Loader2, ShieldCheck } from 'lucide-react'
import { toast } from 'sonner'
import { useDataStore } from '@/store/dataStore'
import { PIPELINE_STAGES } from '@/lib/pipelineStages'
import { KanbanCard } from '@/components/kanban/KanbanCard'
import { EmptyState } from '@/components/common/EmptyState'
import { ApiError } from '@/lib/apiClient'
import type { EstadoPipeline } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function PipelineView() {
  const { postulaciones, vacantes, fetchPostulaciones, fetchVacantes, authorizePostulacion, movePostulacionStage } = useDataStore()
  const [loading, setLoading] = useState(true)
  const [vacanteFilter, setVacanteFilter] = useState<string>('todas')

  useEffect(() => {
    Promise.all([fetchPostulaciones(), fetchVacantes()])
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchPostulaciones, fetchVacantes])

  const filtered = useMemo(
    () => postulaciones.filter((p) => vacanteFilter === 'todas' || p.vacante_id === vacanteFilter),
    [postulaciones, vacanteFilter]
  )

  const pendientes = filtered.filter((p) => p.estado_pipeline === 'pendiente_autorizacion')

  async function handleAuthorize(id: string) {
    try {
      await authorizePostulacion(id)
      toast.success('Postulación autorizada e ingresada al pipeline')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function onDragEnd(result: DropResult) {
    const { destination, draggableId } = result
    if (!destination) return
    const nuevoEstado = destination.droppableId as EstadoPipeline
    try {
      await movePostulacionStage(draggableId, nuevoEstado)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Pipeline de Reclutamiento</h1>
          <p className="text-sm text-slate-500">Arrastra las tarjetas para mover candidatos entre etapas autorizadas</p>
        </div>
        <select
          value={vacanteFilter}
          onChange={(e) => setVacanteFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="todas">Todas las vacantes</option>
          {vacantes.map((v) => (
            <option key={v.id} value={v.id}>
              {v.titulo}
            </option>
          ))}
        </select>
      </div>

      <div>
        <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-amber-700">
          <ShieldCheck size={16} /> Pendientes de autorización ({pendientes.length})
        </h2>
        {pendientes.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-400">
            No hay postulaciones esperando autorización
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-2 rounded-lg border border-amber-100 bg-amber-50/50 p-3 sm:grid-cols-2 lg:grid-cols-3">
            {pendientes.map((p) => (
              <div key={p.id} className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="text-sm font-medium text-slate-800">
                  {p.postulante_nombres} {p.postulante_apellidos}
                </p>
                <p className="text-xs text-slate-500">{p.vacante_titulo}</p>
                <button
                  onClick={() => handleAuthorize(p.id)}
                  className="mt-2 w-full rounded-md bg-brand-600 px-2 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
                >
                  Autorizar ingreso al pipeline
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="Sin postulaciones" description="No hay postulaciones para esta vacante todavía." />
      ) : (
        <DragDropContext onDragEnd={onDragEnd}>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {PIPELINE_STAGES.map((stage) => {
              const items = filtered.filter((p) => p.estado_pipeline === stage.key)
              return (
                <Droppable key={stage.key} droppableId={stage.key}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`w-72 shrink-0 rounded-lg border border-slate-200 bg-slate-100/70 p-2 ${
                        snapshot.isDraggingOver ? 'bg-brand-50' : ''
                      }`}
                    >
                      <div className="mb-2 flex items-center justify-between px-1">
                        <h3 className="text-xs font-semibold uppercase text-slate-600">{stage.label}</h3>
                        <span className="rounded-full bg-white px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
                          {items.length}
                        </span>
                      </div>
                      <div className="min-h-[60px]">
                        {items.map((p, index) => (
                          <KanbanCard key={p.id} postulacion={p} index={index} />
                        ))}
                        {provided.placeholder}
                      </div>
                    </div>
                  )}
                </Droppable>
              )
            })}
          </div>
        </DragDropContext>
      )}
    </div>
  )
}
