import { useEffect, useState } from 'react'
import { Plus, Linkedin, MessageCircle, Link2, Copy, XCircle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function VacantesView() {
  const { vacantes, cargos, postulaciones, fetchVacantes, fetchCargos, fetchPostulaciones, createVacante, publishLinkedIn, shareWhatsApp, cerrarVacante } =
    useDataStore()
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ titulo: '', cargo_id: 0, descripcion: '', fecha_limite: '' })

  useEffect(() => {
    Promise.all([fetchVacantes(), fetchCargos(), fetchPostulaciones()])
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchVacantes, fetchCargos, fetchPostulaciones])

  useEffect(() => {
    if (cargos.length > 0 && form.cargo_id === 0) setForm((f) => ({ ...f, cargo_id: cargos[0].id }))
  }, [cargos, form.cargo_id])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!form.titulo.trim() || !form.fecha_limite || !form.cargo_id) return
    try {
      const v = await createVacante({
        titulo: form.titulo,
        cargo_id: Number(form.cargo_id),
        descripcion: form.descripcion,
        fecha_limite: new Date(form.fecha_limite).toISOString(),
      })
      toast.success(`Vacante "${v.titulo}" publicada`)
      setForm({ titulo: '', cargo_id: cargos[0]?.id ?? 0, descripcion: '', fecha_limite: '' })
      setShowNew(false)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  function publicUrl(slug: string) {
    return `${window.location.origin}/postular/${slug}`
  }

  function copyLink(slug: string) {
    navigator.clipboard?.writeText(publicUrl(slug))
    toast.success('Enlace copiado al portapapeles')
  }

  async function handleShareWhatsApp(id: string) {
    try {
      const url = await shareWhatsApp(id)
      window.open(url, '_blank')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handlePublishLinkedIn(id: string) {
    try {
      await publishLinkedIn(id)
      toast.success('Vacante publicada en LinkedIn')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleCerrar(id: string) {
    try {
      await cerrarVacante(id)
      toast.success('Vacante cerrada')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const badgeTone = (estado: string) => (estado === 'activa' ? 'green' : estado === 'expirada' ? 'red' : 'slate') as const

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Vacantes</h1>
          <p className="text-sm text-slate-500">Creación, publicación y difusión multicanal de vacantes</p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus size={16} /> Nueva Vacante
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Título</th>
                <th className="px-4 py-3">Cargo</th>
                <th className="px-4 py-3">Vence</th>
                <th className="px-4 py-3">Postulaciones</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Canales</th>
                <th className="px-4 py-3">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {vacantes.map((v) => {
                const cargo = cargos.find((c) => c.id === v.cargo_id)
                const count = postulaciones.filter((p) => p.vacante_id === v.id).length
                return (
                  <tr key={v.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-medium text-slate-800">{v.titulo}</td>
                    <td className="px-4 py-3 text-slate-600">{cargo?.nombre}</td>
                    <td className="px-4 py-3 text-slate-600">{new Date(v.fecha_limite).toLocaleDateString('es-EC')}</td>
                    <td className="px-4 py-3 text-slate-600">{count}</td>
                    <td className="px-4 py-3">
                      <Badge tone={badgeTone(v.estado)}>{v.estado}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {v.linkedin_post_id && <Badge tone="blue">LinkedIn</Badge>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <button
                          title="Copiar enlace público"
                          onClick={() => copyLink(v.slug)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Copy size={15} />
                        </button>
                        <a
                          href={publicUrl(v.slug)}
                          target="_blank"
                          rel="noreferrer"
                          title="Ver postulación pública"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Link2 size={15} />
                        </a>
                        <button
                          title="Publicar en LinkedIn"
                          onClick={() => handlePublishLinkedIn(v.id)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-blue-50 hover:text-blue-700"
                        >
                          <Linkedin size={15} />
                        </button>
                        <button
                          title="Compartir en WhatsApp"
                          onClick={() => handleShareWhatsApp(v.id)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-emerald-50 hover:text-emerald-700"
                        >
                          <MessageCircle size={15} />
                        </button>
                        {v.estado !== 'cerrada' && (
                          <button
                            title="Cerrar vacante"
                            onClick={() => handleCerrar(v.id)}
                            className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-700"
                          >
                            <XCircle size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      )}

      <Modal open={showNew} onClose={() => setShowNew(false)} title="Nueva Vacante" wide>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Título de la vacante</label>
            <input
              required
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="Ej. Desarrollador Backend Senior"
            />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Cargo</label>
              <select
                value={form.cargo_id}
                onChange={(e) => setForm({ ...form, cargo_id: Number(e.target.value) })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {cargos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Fecha límite</label>
              <input
                required
                type="date"
                value={form.fecha_limite}
                onChange={(e) => setForm({ ...form, fecha_limite: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Descripción</label>
            <textarea
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              rows={4}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Documento descriptivo (.pdf, .docx, .doc)</label>
            <input type="file" accept=".pdf,.doc,.docx" className="w-full text-sm text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm" />
            <p className="mt-1 text-xs text-slate-400">La subida de archivos a almacenamiento se implementará en una fase posterior.</p>
          </div>
          <button type="submit" className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700">
            Publicar Vacante
          </button>
        </form>
      </Modal>
    </div>
  )
}
