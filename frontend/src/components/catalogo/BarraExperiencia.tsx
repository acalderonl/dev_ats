import { EXPERIENCIA_TRAMOS, type ExperienciaRequerida } from '@/types'

/** Barra de tramos de experiencia: se elige uno y se rellenan los anteriores. */
export function BarraExperiencia({
  valor,
  onChange,
}: {
  valor: ExperienciaRequerida | null
  onChange: (valor: ExperienciaRequerida | null) => void
}) {
  const indiceElegido = EXPERIENCIA_TRAMOS.findIndex((t) => t.valor === valor)

  return (
    <div>
      <div className="flex overflow-hidden rounded-lg border border-slate-300">
        {EXPERIENCIA_TRAMOS.map((tramo, i) => {
          const elegido = i === indiceElegido
          const alcanzado = indiceElegido >= 0 && i <= indiceElegido
          return (
            <button
              key={tramo.valor}
              type="button"
              aria-pressed={elegido}
              // Volver a pulsar el tramo elegido lo deja sin especificar.
              onClick={() => onChange(elegido ? null : tramo.valor)}
              className={`flex-1 border-r border-slate-200 px-2 py-2.5 text-xs font-medium transition-colors last:border-r-0 ${
                elegido
                  ? 'bg-brand-600 text-white'
                  : alcanzado
                    ? 'bg-brand-100 text-brand-700 hover:bg-brand-200'
                    : 'bg-white text-slate-500 hover:bg-slate-50'
              }`}
            >
              {tramo.etiqueta}
            </button>
          )
        })}
      </div>
      <p className="mt-1 text-xs text-slate-400">
        {valor
          ? `Se exigirá: ${EXPERIENCIA_TRAMOS[indiceElegido].etiqueta}. Pulsa de nuevo para quitarlo.`
          : 'Sin especificar.'}
      </p>
    </div>
  )
}
