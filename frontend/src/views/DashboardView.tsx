import { useEffect, useState } from 'react'
import { Briefcase, Users, TrendingUp, CalendarClock, Loader2 } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { toast } from 'sonner'
import { StatCard } from '@/components/common/StatCard'
import { Card, CardBody, CardHeader } from '@/components/common/Card'
import { useDataStore } from '@/store/dataStore'
import { dashboardService } from '@/services/dashboardService'
import { ApiError } from '@/lib/apiClient'
import type { DashboardMetrics } from '@/types'
import { PIPELINE_STAGES } from '@/lib/pipelineStages'

const PIPELINE_COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#f59e0b', '#ec4899', '#10b981', '#ef4444']
const ORIGEN_COLORS: Record<string, string> = { LinkedIn: '#0a66c2', WhatsApp: '#25d366', Directo: '#64748b' }

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function DashboardView() {
  const { vacantes, fetchVacantes } = useDataStore()
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([dashboardService.metrics(), fetchVacantes()])
      .then(([m]) => setMetrics(m))
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchVacantes])

  if (loading || !metrics) {
    return (
      <div className="flex justify-center py-12 text-slate-400">
        <Loader2 className="animate-spin" size={24} />
      </div>
    )
  }

  const pipelineData = PIPELINE_STAGES.map((stage) => ({
    name: stage.label,
    total: metrics.postulaciones_por_etapa.find((e) => e.estado === stage.key)?.total ?? 0,
  }))

  const origenCounts = ['LinkedIn', 'WhatsApp', 'Directo'].map((origen) => ({
    name: origen,
    value: metrics.postulaciones_por_origen.find((o) => o.origen === origen)?.total ?? 0,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">Resumen operativo del proceso de reclutamiento</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Vacantes Activas"
          value={metrics.vacantes_activas}
          icon={Briefcase}
          tone="blue"
          hint={`${metrics.vacantes_expiradas} expiradas`}
        />
        <StatCard label="Postulaciones Totales" value={metrics.postulaciones_totales} icon={Users} tone="green" />
        <StatCard label="Vacantes Registradas" value={vacantes.length} icon={TrendingUp} tone="purple" />
        <StatCard label="Entrevistas Pendientes" value={metrics.entrevistas_pendientes} icon={CalendarClock} tone="amber" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <h2 className="text-sm font-semibold text-slate-800">Postulantes por etapa del pipeline</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pipelineData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={70} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                  {pipelineData.map((_, i) => (
                    <Cell key={i} fill={PIPELINE_COLORS[i % PIPELINE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold text-slate-800">Origen de postulaciones</h2>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={origenCounts} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}>
                  {origenCounts.map((entry, i) => (
                    <Cell key={i} fill={ORIGEN_COLORS[entry.name] ?? '#94a3b8'} />
                  ))}
                </Pie>
                <Legend verticalAlign="bottom" height={30} />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-sm font-semibold text-slate-800">Vacantes por estado</h2>
        </CardHeader>
        <CardBody className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {vacantes.map((v) => (
            <div key={v.id} className="rounded-lg border border-slate-100 p-3">
              <p className="truncate text-sm font-medium text-slate-800">{v.titulo}</p>
              <p className="mt-1 text-xs text-slate-500">
                Vence: {new Date(v.fecha_limite).toLocaleDateString('es-EC')}
              </p>
              <p className="mt-1 text-xs font-medium capitalize text-brand-600">{v.estado}</p>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  )
}
