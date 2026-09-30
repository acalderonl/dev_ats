import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'
import type { RolNombre } from '@/types'

const ROLE_LABELS: Record<RolNombre, string> = {
  super_admin: 'Super Admin',
  reclutador: 'Reclutador / Empleador',
  entrevistador: 'Entrevistador / Evaluador',
}

const ROLE_TONE: Record<RolNombre, 'purple' | 'blue' | 'amber'> = {
  super_admin: 'purple',
  reclutador: 'blue',
  entrevistador: 'amber',
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function UsuariosView() {
  const { usuarios, fetchUsuarios, setUsuarioRol, toggleUsuarioActivo } = useDataStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchUsuarios()
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [fetchUsuarios])

  async function handleRolChange(id: string, rol: RolNombre) {
    try {
      await setUsuarioRol(id, rol)
      toast.success('Rol actualizado')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleToggleActivo(id: string, activoActual: boolean) {
    try {
      await toggleUsuarioActivo(id, !activoActual)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Usuarios y Roles</h1>
        <p className="text-sm text-slate-500">Control de acceso basado en roles (RBAC). Los usuarios se registran ellos mismos desde el login.</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Correo</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {u.nombres} {u.apellidos}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.rol}
                      onChange={(e) => handleRolChange(u.id, e.target.value as RolNombre)}
                      className="rounded-md border border-slate-200 px-2 py-1 text-xs"
                    >
                      {Object.entries(ROLE_LABELS).map(([key, label]) => (
                        <option key={key} value={key}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={u.activo ? 'green' : 'slate'}>{u.activo ? 'Activo' : 'Inactivo'}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggleActivo(u.id, u.activo)}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                    >
                      {u.activo ? 'Desactivar' : 'Activar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        {(Object.keys(ROLE_LABELS) as RolNombre[]).map((rol) => (
          <Badge key={rol} tone={ROLE_TONE[rol]}>
            {ROLE_LABELS[rol]}
          </Badge>
        ))}
      </div>
    </div>
  )
}
