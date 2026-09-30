import { Linkedin } from 'lucide-react'

export function VacanteExpiradaView() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600 text-xl font-bold text-white">
        ATS
      </div>
      <h1 className="mt-6 text-xl font-semibold text-slate-900">Esta vacante ha expirado</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Lo sentimos, esta oferta laboral ya no está disponible. Revisa nuestro LinkedIn para más información sobre
        nuevas oportunidades.
      </p>
      <a
        href="https://www.linkedin.com"
        target="_blank"
        rel="noreferrer"
        className="mt-6 flex items-center gap-2 rounded-lg bg-[#0a66c2] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
      >
        <Linkedin size={18} /> Ver perfil de LinkedIn
      </a>
    </div>
  )
}
