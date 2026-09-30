import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard,
  Briefcase,
  KanbanSquare,
  Users,
  ClipboardCheck,
  ShieldCheck,
  Building2,
  X,
} from 'lucide-react'
import type { RolNombre } from '@/types'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
  roles: RolNombre[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['super_admin', 'reclutador', 'entrevistador'] },
  { to: '/cargos', label: 'Cargos', icon: Building2, roles: ['super_admin', 'reclutador'] },
  { to: '/vacantes', label: 'Vacantes', icon: Briefcase, roles: ['super_admin', 'reclutador'] },
  { to: '/pipeline', label: 'Pipeline', icon: KanbanSquare, roles: ['super_admin', 'reclutador'] },
  { to: '/contactos', label: 'Contactos', icon: Users, roles: ['super_admin', 'reclutador'] },
  { to: '/evaluaciones', label: 'Evaluaciones', icon: ClipboardCheck, roles: ['super_admin', 'reclutador', 'entrevistador'] },
  { to: '/usuarios', label: 'Usuarios y Roles', icon: ShieldCheck, roles: ['super_admin'] },
]

export function Sidebar({
  role,
  mobileOpen,
  onCloseMobile,
}: {
  role: RolNombre
  mobileOpen: boolean
  onCloseMobile: () => void
}) {
  const items = NAV_ITEMS.filter((i) => i.roles.includes(role))

  const content = (
    <nav className="flex h-full flex-col gap-1 p-3">
      <div className="flex items-center gap-2 px-2 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
          ATS
        </div>
        <span className="text-sm font-semibold text-slate-800">Sistema ATS</span>
      </div>
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onCloseMobile}
          className={({ isActive }) =>
            clsx(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
            )
          }
        >
          <Icon size={18} />
          {label}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <>
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white lg:block">{content}</aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={onCloseMobile} />
          <div className="relative z-10 h-full w-64 bg-white shadow-xl">
            <button onClick={onCloseMobile} className="absolute right-2 top-2 rounded-md p-1 text-slate-400 hover:bg-slate-100">
              <X size={18} />
            </button>
            {content}
          </div>
        </div>
      )}
    </>
  )
}
