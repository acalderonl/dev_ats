import { LogOut, Menu } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Super Admin',
  reclutador: 'Reclutador / Empleador',
  entrevistador: 'Entrevistador / Evaluador',
}

export function Topbar({ onOpenMobile }: { onOpenMobile: () => void }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
      <button onClick={onOpenMobile} className="rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden">
        <Menu size={20} />
      </button>
      <div className="hidden sm:block" />
      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm font-medium text-slate-800">{user.nombres} {user.apellidos}</p>
          <p className="text-xs text-slate-400">{ROLE_LABELS[user.rol]}</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
          {user.nombres[0]}
          {user.apellidos[0]}
        </div>
        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          title="Cerrar sesión"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  )
}
