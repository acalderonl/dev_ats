import { Plus, Trash2 } from 'lucide-react'
import type { CampoPersonalizado } from '@/types'

const MAXIMO = 20

/**
 * Campos que inventa quien publica: primero la etiqueta, luego el valor.
 *
 * Las etiquetas no se pueden repetir —dos campos "Ciudad" harían ambigua la lectura
 * del post— y el aviso sale aquí, junto a la fila, en vez de esperar al guardado.
 */
export function CamposPersonalizados({
  campos,
  onChange,
}: {
  campos: CampoPersonalizado[]
  onChange: (campos: CampoPersonalizado[]) => void
}) {
  const normalizada = (texto: string) => texto.trim().toLowerCase()

  function etiquetaRepetida(indice: number): boolean {
    const actual = normalizada(campos[indice].etiqueta)
    if (!actual) return false
    return campos.some((c, i) => i !== indice && normalizada(c.etiqueta) === actual)
  }

  function actualizar(indice: number, cambios: Partial<CampoPersonalizado>) {
    onChange(campos.map((c, i) => (i === indice ? { ...c, ...cambios } : c)))
  }

  return (
    <div className="space-y-2">
      {campos.map((campo, indice) => {
        const repetida = etiquetaRepetida(indice)
        return (
          <div key={indice} className="space-y-1">
            <div className="flex items-start gap-2">
              <input
                value={campo.etiqueta}
                onChange={(e) => actualizar(indice, { etiqueta: e.target.value })}
                placeholder="Nombre del campo (ej. Ciudad)"
                className={`w-2/5 rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 ${
                  repetida
                    ? 'border-red-400 focus:border-red-500 focus:ring-red-500'
                    : 'border-slate-300 focus:border-brand-500 focus:ring-brand-500'
                }`}
              />
              <input
                value={campo.valor}
                onChange={(e) => actualizar(indice, { valor: e.target.value })}
                placeholder="Contenido"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <button
                type="button"
                onClick={() => onChange(campos.filter((_, i) => i !== indice))}
                title="Quitar este campo"
                className="mt-1 rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 size={15} />
              </button>
            </div>
            {repetida && (
              <p className="pl-1 text-xs text-red-600">
                Ya hay otro campo con este nombre. No se pueden repetir.
              </p>
            )}
          </div>
        )
      })}

      <button
        type="button"
        onClick={() => onChange([...campos, { etiqueta: '', valor: '' }])}
        disabled={campos.length >= MAXIMO}
        title={campos.length >= MAXIMO ? `Máximo ${MAXIMO} campos` : undefined}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-slate-300 py-2 text-sm text-slate-500 hover:border-brand-400 hover:text-brand-600 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-slate-300 disabled:hover:text-slate-500"
      >
        <Plus size={15} />
        {campos.length >= MAXIMO ? `Máximo ${MAXIMO}` : 'Agregar campo'}
      </button>
    </div>
  )
}
