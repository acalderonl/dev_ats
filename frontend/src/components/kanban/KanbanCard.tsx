import { Draggable } from '@hello-pangea/dnd'
import { Briefcase } from 'lucide-react'
import { Badge } from '@/components/common/Badge'
import type { Postulacion } from '@/types'

const ORIGEN_TONE: Record<string, 'blue' | 'green' | 'slate'> = { LinkedIn: 'blue', WhatsApp: 'green', Directo: 'slate' }

export function KanbanCard({ postulacion, index }: { postulacion: Postulacion; index: number }) {
  return (
    <Draggable draggableId={postulacion.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`mb-2 rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition-shadow ${
            snapshot.isDragging ? 'shadow-md ring-2 ring-brand-300' : ''
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">
              {postulacion.postulante_nombres} {postulacion.postulante_apellidos}
            </p>
            {postulacion.match_score !== null && (
              <span className="shrink-0 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500">
                {postulacion.match_score}%
              </span>
            )}
          </div>
          <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
            <Briefcase size={12} /> {postulacion.vacante_titulo}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <Badge tone={ORIGEN_TONE[postulacion.origen]}>{postulacion.origen}</Badge>
            {!postulacion.autorizado_por && <Badge tone="amber">Sin autorizar</Badge>}
          </div>
        </div>
      )}
    </Draggable>
  )
}
