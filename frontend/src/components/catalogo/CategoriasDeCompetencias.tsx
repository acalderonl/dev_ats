import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Check, Loader2, Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { competenciasService } from '@/services/competenciasService'
import { ApiError } from '@/lib/apiClient'
import type { CompetenciaSugerida, GrupoPorClasificacion, TipoCompetencia } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/** Margen tras salir el cursor antes de cerrar solo. */
const MS_ANTES_DE_CERRAR = 2000

/**
 * Botones por clasificación de cargo que despliegan lo que ya piden otros cargos.
 *
 * Reaprovechar en lugar de volver a escribir: al crear un cargo de Tecnología, lo útil
 * es ver qué piden los demás cargos de Tecnología. Dentro de cada grupo van primero las
 * más usadas, porque si cinco cargos del área piden lo mismo este probablemente también.
 *
 * El panel se abre **hacia arriba**, sobre los botones. Así la fila de botones no se
 * mueve de sitio al abrirse: lo que acabas de pulsar sigue donde estaba.
 *
 * La clasificación del cargo que se está editando va primera y marcada, que es el grupo
 * que casi siempre se quiere.
 */
export function CategoriasDeCompetencias({
  tipo,
  clasificacionActual,
  yaElegidas,
  onElegir,
}: {
  tipo: TipoCompetencia
  /** La clasificación del cargo en edición, para destacar su grupo. */
  clasificacionActual: number | null
  /** Ids ya en la lista: se marcan y no se pueden añadir dos veces. */
  yaElegidas: Set<number>
  onElegir: (competencia: CompetenciaSugerida) => void
}) {
  const [grupos, setGrupos] = useState<GrupoPorClasificacion[]>([])
  const [cargando, setCargando] = useState(true)
  const [abierto, setAbierto] = useState<number | null>(null)
  const temporizadorDeCierre = useRef<number | null>(null)

  const cancelarCierre = useCallback(() => {
    if (temporizadorDeCierre.current !== null) {
      clearTimeout(temporizadorDeCierre.current)
      temporizadorDeCierre.current = null
    }
  }, [])

  /**
   * Cierra solo al salir el cursor, con margen.
   *
   * Los 2 segundos son para no castigar el pulso: cruzar fuera del panel camino de un
   * chip del borde no debería cerrarlo. Si el cursor vuelve antes, se cancela.
   */
  const programarCierre = useCallback(() => {
    cancelarCierre()
    temporizadorDeCierre.current = window.setTimeout(() => setAbierto(null), MS_ANTES_DE_CERRAR)
  }, [cancelarCierre])

  // Si el modal se cierra con el panel abierto, el temporizador seguiría vivo y
  // llamaría a `setAbierto` sobre un componente ya desmontado.
  useEffect(() => cancelarCierre, [cancelarCierre])

  useEffect(() => {
    let vigente = true
    setCargando(true)
    competenciasService
      .porClasificacion(tipo)
      .then((datos) => {
        if (vigente) setGrupos(datos)
      })
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [tipo])

  // La clasificación del cargo en edición, primera.
  const ordenados = useMemo(() => {
    if (clasificacionActual === null) return grupos
    return [...grupos].sort((a, b) => {
      if (a.clasificacion_id === clasificacionActual) return -1
      if (b.clasificacion_id === clasificacionActual) return 1
      return 0
    })
  }, [grupos, clasificacionActual])

  const grupoAbierto = ordenados.find((g) => g.clasificacion_id === abierto) ?? null

  if (cargando) {
    return (
      <div className="flex items-center gap-2 py-2 text-xs text-slate-400">
        <Loader2 size={13} className="animate-spin" /> Buscando lo que ya usan otros cargos...
      </div>
    )
  }

  // Sin cargos previos no hay nada que reaprovechar. Mejor no pintar botones vacíos.
  if (ordenados.length === 0) return null

  return (
    // Los eventos van en el contenedor, no en el panel: así moverse del panel a los
    // botones (o al revés) no cuenta como salir, que es lo que se hace al abrir otra
    // categoría sin cerrar la anterior.
    <div
      className="relative"
      onMouseLeave={abierto === null ? undefined : programarCierre}
      onMouseEnter={cancelarCierre}
    >
      {/* El panel va **flotando** sobre los botones (`absolute bottom-full`), no en el
          flujo. Si ocupara sitio, al abrirlo empujaría la fila de botones hacia abajo
          —94px, medidos— y lo que acabas de pulsar se escaparía de debajo del cursor.
          Flotando, sale hacia arriba y nada se mueve. */}
      {grupoAbierto && (
        <div className="animate-desplegar-arriba absolute bottom-full left-0 right-0 z-20 mb-2 overflow-hidden rounded-lg border border-brand-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-brand-100 px-3 py-2">
            <span className="text-xs font-medium text-brand-900">
              Ya se usan en cargos de {grupoAbierto.clasificacion}
            </span>
            <button
              type="button"
              onClick={() => setAbierto(null)}
              className="rounded p-0.5 text-brand-400 hover:bg-brand-100 hover:text-brand-700"
            >
              <X size={14} />
            </button>
          </div>

          <div className="flex max-h-56 flex-wrap gap-1.5 overflow-y-auto p-3">
            {grupoAbierto.competencias.map((competencia) => {
              const puesta = yaElegidas.has(competencia.id)
              return (
                <button
                  key={competencia.id}
                  type="button"
                  disabled={puesta}
                  onClick={() => onElegir(competencia)}
                  title={
                    puesta
                      ? 'Ya está en la lista'
                      : `La usan ${competencia.usos} cargo(s) de ${grupoAbierto.clasificacion}`
                  }
                  className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors ${
                    puesta
                      ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                      : 'border-brand-300 bg-white text-brand-800 hover:border-brand-500 hover:bg-brand-100'
                  }`}
                >
                  {puesta ? <Check size={11} /> : <Plus size={11} />}
                  {competencia.nombre}
                  <span className={puesta ? 'text-slate-400' : 'text-brand-400'}>{competencia.usos}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {ordenados.map((grupo) => {
          const estaAbierto = abierto === grupo.clasificacion_id
          const esLaDelCargo = grupo.clasificacion_id === clasificacionActual
          return (
            <button
              key={grupo.clasificacion_id ?? 'sin'}
              type="button"
              onClick={() => setAbierto(estaAbierto ? null : grupo.clasificacion_id)}
              className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors ${
                estaAbierto
                  ? 'border-brand-500 bg-brand-600 text-white'
                  : esLaDelCargo
                    ? 'border-brand-300 bg-brand-50 text-brand-800 hover:bg-brand-100'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900'
              }`}
            >
              <Plus
                size={13}
                className={`transition-transform duration-200 ${estaAbierto ? 'rotate-45' : ''}`}
              />
              {grupo.clasificacion}
              <span className={estaAbierto ? 'text-brand-200' : 'text-slate-400'}>
                {grupo.competencias.length}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
