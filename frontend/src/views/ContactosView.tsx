import { useEffect, useMemo, useState } from 'react'
import { Search, Download, Tag, Mail, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { EmptyState } from '@/components/common/EmptyState'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function ContactosView() {
  const { contactos, fetchContactos } = useDataStore()
  const [query, setQuery] = useState('')
  const [nivelFilter, setNivelFilter] = useState('todos')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchContactos({ q: query || undefined, nivel_instruccion: nivelFilter === 'todos' ? undefined : nivelFilter })
        .catch((err) => toast.error(errorMessage(err)))
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(timeout)
  }, [query, nivelFilter, fetchContactos])

  const niveles = useMemo(
    () => Array.from(new Set(contactos.map((p) => p.nivel_instruccion).filter((n): n is string => !!n))),
    [contactos]
  )

  function exportar() {
    toast.success(`Exportando ${contactos.length} contactos (CSV simulado)`)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Directorio de Contactos</h1>
          <p className="text-sm text-slate-500">Banco de talento histórico de todos los postulantes</p>
        </div>
        <button onClick={exportar} className="flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
          <Download size={16} /> Exportar
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar por nombre, título o cédula..."
            className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <select value={nivelFilter} onChange={(e) => setNivelFilter(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="todos">Todos los niveles</option>
          {niveles.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : contactos.length === 0 ? (
        <EmptyState icon={Search} title="Sin resultados" description="Ajusta los filtros de búsqueda para encontrar candidatos." />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Cédula</th>
                <th className="px-4 py-3">Contacto</th>
                <th className="px-4 py-3">Nivel</th>
                <th className="px-4 py-3">Último cargo</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Postulaciones</th>
                <th className="px-4 py-3">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {contactos.map((p) => (
                <tr key={p.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {p.nombres} {p.apellidos}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{p.cedula}</td>
                  <td className="px-4 py-3 text-slate-600">
                    <div className="flex flex-col">
                      <span>{p.email}</span>
                      <span className="text-xs text-slate-400">{p.telefono}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{p.nivel_instruccion ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600">{p.titulos?.[0] ?? '—'}</td>
                  <td className="px-4 py-3">
                    <Badge tone="blue">{p.ultimo_estado_pipeline ?? '—'}</Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{p.total_postulaciones}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <a href={`mailto:${p.email}`} title="Enviar correo" className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
                        <Mail size={15} />
                      </a>
                      <button
                        title="Etiquetar candidato"
                        onClick={() => toast.success('Candidato etiquetado')}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      >
                        <Tag size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
