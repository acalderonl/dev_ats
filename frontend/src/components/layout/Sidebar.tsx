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
  Settings,
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
  { to: '/configuracion', label: 'Configuración', icon: Settings, roles: ['super_admin'] },
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
    <nav className="flex h-full flex-col gap-1 bg-brand-900 p-3">
      <div className="flex items-center gap-2.5 px-2 py-3">
        {/* El escudo es monocromo (#20395f): sobre el azul oscuro se perdería. El
            filtro lo deja en blanco, que es como la institución lo usa sobre azul. */}
        <img src="/escudo-anai.svg" alt="" className="h-10 w-auto shrink-0 brightness-0 invert" />
        <div className="min-w-0">
          <span className="block text-sm font-semibold leading-tight tracking-wide text-white">ANAI</span>
          <span className="block truncate text-[11px] leading-tight text-brand-200">
            Selección de personal
          </span>
        </div>
      </div>

      <div className="mb-2 border-t border-white/10" />

      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onCloseMobile}
          className={({ isActive }) =>
            clsx(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-white/15 text-white'
                : 'text-brand-100 hover:bg-white/10 hover:text-white'
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
      <aside className="hidden w-60 shrink-0 bg-brand-900 lg:block">{content}</aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={onCloseMobile} />
          <div className="relative z-10 h-full w-64 bg-brand-900 shadow-xl">
            <button
              onClick={onCloseMobile}
              className="absolute right-2 top-2 rounded-md p-1 text-brand-200 hover:bg-white/10 hover:text-white"
            >
              <X size={18} />
            </button>
            {content}
          </div>
        </div>
      )}
    </>
  )
}
