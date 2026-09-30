import type { EstadoPipeline } from '@/types'

export const PIPELINE_STAGES: { key: EstadoPipeline; label: string }[] = [
  { key: 'postulacion_revisada', label: 'Postulación Revisada' },
  { key: 'en_revision', label: 'En Revisión' },
  { key: 'preseleccionado', label: 'Preseleccionado' },
  { key: 'evaluaciones', label: 'Evaluaciones' },
  { key: 'entrevista', label: 'Entrevista' },
  { key: 'contratado', label: 'Contratado' },
  { key: 'descartado', label: 'Descartado' },
]
