import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AlertTriangle, Check, Loader2 } from 'lucide-react'
import { configuracionService } from '@/services/vacantesService'
import { ApiError } from '@/lib/apiClient'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/**
 * Página a la que LinkedIn devuelve al usuario tras dar (o negar) permiso.
 *
 * LinkedIn redirige el **navegador** aquí con `?code=...&state=...`; esta página
 * reenvía esos dos valores al backend con la sesión del usuario. Por eso la URL de
 * retorno apunta al frontend y no a la API: así el token queda atado a quien de
 * verdad inició la conexión, no a quien consiga llamar al endpoint.
 */
export function LinkedInRetornoView() {
  const [params] = useSearchParams()
  const navegar = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [listo, setListo] = useState(false)
  // React 18 en modo estricto monta dos veces en desarrollo. El código de LinkedIn
  // es de un solo uso: canjearlo dos veces falla la segunda.
  const yaCanjeado = useRef(false)

  useEffect(() => {
    if (yaCanjeado.current) return
    yaCanjeado.current = true

    // LinkedIn avisa del rechazo por la propia URL, no con un error.
    const denegado = params.get('error')
    if (denegado) {
      setError(
        params.get('error_description') ||
          'No se concedió el permiso en LinkedIn, así que no se conectó la cuenta.',
      )
      return
    }

    const code = params.get('code')
    const state = params.get('state')
    if (!code || !state) {
      setError('LinkedIn no devolvió los datos esperados. Vuelve a intentar la conexión.')
      return
    }

    configuracionService
      .terminarConexionLinkedIn({ code, state })
      .then(() => {
        setListo(true)
        setTimeout(() => navegar('/configuracion', { replace: true }), 1500)
      })
      .catch((err) => setError(errorMessage(err)))
  }, [params, navegar])

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        {error ? (
          <>
            <AlertTriangle className="mx-auto text-red-500" size={32} />
            <h1 className="mt-4 text-base font-semibold text-slate-900">No se pudo conectar</h1>
            <p className="mt-2 text-sm text-slate-600">{error}</p>
            <button
              onClick={() => navegar('/configuracion', { replace: true })}
              className="mt-6 w-full rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Volver a Configuración
            </button>
          </>
        ) : listo ? (
          <>
            <Check className="mx-auto text-emerald-500" size={32} />
            <h1 className="mt-4 text-base font-semibold text-slate-900">Cuenta conectada</h1>
            <p className="mt-2 text-sm text-slate-600">Volviendo a Configuración...</p>
          </>
        ) : (
          <>
            <Loader2 className="mx-auto animate-spin text-brand-600" size={32} />
            <h1 className="mt-4 text-base font-semibold text-slate-900">Conectando con LinkedIn</h1>
            <p className="mt-2 text-sm text-slate-600">Un momento.</p>
          </>
        )}
      </div>
    </div>
  )
}
