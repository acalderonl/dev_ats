import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

const DEMO_ACCOUNTS = [
  { email: 'admin@atsdemo.com', rol: 'Super Admin' },
  { email: 'reclutador@atsdemo.com', rol: 'Reclutador / Empleador' },
  { email: 'entrevistador@atsdemo.com', rol: 'Entrevistador / Evaluador' },
]

export function LoginView() {
  const { user, login } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail] = useState('reclutador@atsdemo.com')
  const [password, setPassword] = useState('Demo1234!')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    const result = await login(email, password)
    setLoading(false)
    if (result.ok) {
      toast.success('Sesión iniciada correctamente')
      navigate('/')
    } else {
      toast.error(result.message)
    }
  }

  return (
    // Degradado con los dos azules de la institución: el institucional y el oscuro
    // de las franjas del sitio.
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-700 via-brand-600 to-brand-900 px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
        <div className="mb-6 text-center">
          <img src="/escudo-anai.svg" alt="Escudo de la ANAI" className="mx-auto mb-4 h-20 w-auto" />
          <h1 className="text-xl font-semibold tracking-wide text-escudo">ANAI</h1>
          <p className="mt-0.5 text-xs leading-snug text-slate-500">
            Academia Naval Almirante Illingworth
          </p>
          <p className="mt-4 text-sm font-medium text-slate-700">Selección de personal</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Correo electrónico</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:opacity-60"
          >
            {loading && <Loader2 size={16} className="animate-spin" />}
            Ingresar
          </button>
        </form>
        <div className="mt-4 space-y-1 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
          <p className="font-medium text-slate-600">Cuentas de demo (contraseña: Demo1234!)</p>
          {DEMO_ACCOUNTS.map((acc) => (
            <p key={acc.email}>
              {acc.email} — {acc.rol}
            </p>
          ))}
        </div>
      </div>
    </div>
  )
}
