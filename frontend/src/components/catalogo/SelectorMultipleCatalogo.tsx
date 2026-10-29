import { Plus, Settings, Trash2 } from 'lucide-react'
import type { CatalogoItem, EstadoEducacion } from '@/types'
import { MAXIMO_EDUCACION } from '@/types'

/** Una fila del selector: el valor elegido y, si el campo lo pide, su estado. */
export interface FilaDeCatalogo {
  catalogo_id: number | null
  estado?: EstadoEducacion
}

/**
 * Selector de catálogo que admite varias filas, con tope.
 *
 * El engranaje vive en la **cabecera**, junto a la etiqueta, y no dentro de cada fila:
 * así no se desplaza hacia abajo al añadir una fila nueva, y además no tiene sentido
 * repetirlo, porque gestiona el mismo catálogo para todas.
 */
export function SelectorMultipleCatalogo({
  label,
  requerido,
  filas,
  onChange,
  items,
  onGestionar,
  conEstado = false,
  maximo = MAXIMO_EDUCACION,
  textoAgregar,
}: {
  label: string
  requerido?: boolean
  filas: FilaDeCatalogo[]
  onChange: (filas: FilaDeCatalogo[]) => void
  items: CatalogoItem[]
  onGestionar: () => void
  /** Añade el par Completa / En curso a cada fila (solo lo usa el nivel de educación). */
  conEstado?: boolean
  maximo?: number
  textoAgregar: string
}) {
  const alTope = filas.length >= maximo
  const yaElegidos = filas.map((f) => f.catalogo_id).filter((id): id is number => id !== null)

  function actualizar(indice: number, cambios: Partial<FilaDeCatalogo>) {
    onChange(filas.map((f, i) => (i === indice ? { ...f, ...cambios } : f)))
  }

  function agregar() {
    if (alTope) return
    onChange([...filas, { catalogo_id: null, ...(conEstado ? { estado: 'completa' as const } : {}) }])
  }

  function quitar(indice: number) {
    const restantes = filas.filter((_, i) => i !== indice)
    onChange(restantes.length > 0 ? restantes : [{ catalogo_id: null, ...(conEstado ? { estado: 'completa' as const } : {}) }])
  }

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2">
        <label className="text-sm font-medium text-slate-700">
          {label} {requerido && <span className="text-red-500">*</span>}
        </label>
        <button
          type="button"
          onClick={onGestionar}
          title={`Gestionar ${label.toLowerCase()}`}
          className="shrink-0 rounded-lg border border-slate-300 px-2 py-1 text-slate-500 transition-colors hover:bg-slate-50 hover:text-brand-600"
        >
          <Settings size={15} />
        </button>
      </div>

      <div className="space-y-2">
        {filas.map((fila, i) => {
          // Un valor ya elegido en otra fila no vuelve a ofrecerse: no tiene sentido
          // exigir dos veces el mismo nivel, y la base lo rechazaría igualmente.
          const disponibles = items.filter(
            (item) => (item.activo || item.id === fila.catalogo_id) && (!yaElegidos.includes(item.id) || item.id === fila.catalogo_id)
          )
          return (
            <div key={i} className="flex gap-2">
              <select
                required={requerido && i === 0}
                value={fila.catalogo_id ?? ''}
                onChange={(e) => actualizar(i, { catalogo_id: e.target.value ? Number(e.target.value) : null })}
                className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">Selecciona...</option>
                {disponibles.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nombre}
                    {!item.activo ? ' (inactivo)' : ''}
                  </option>
                ))}
              </select>

              {conEstado && (
                <div className="flex shrink-0 overflow-hidden rounded-lg border border-slate-300">
                  {(['completa', 'en_curso'] as EstadoEducacion[]).map((estado) => (
                    <button
                      key={estado}
                      type="button"
                      onClick={() => actualizar(i, { estado })}
                      className={`px-3 py-2 text-xs font-medium transition-colors ${
                        fila.estado === estado
                          ? 'bg-brand-600 text-white'
                          : 'bg-white text-slate-500 hover:bg-slate-50'
                      }`}
                    >
                      {estado === 'completa' ? 'Completa' : 'En curso'}
                    </button>
                  ))}
                </div>
              )}

              {filas.length > 1 && (
                <button
                  type="button"
                  onClick={() => quitar(i)}
                  title="Quitar"
                  className="shrink-0 rounded-lg border border-slate-300 px-2 text-slate-300 transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          )
        })}

        <button
          type="button"
          onClick={agregar}
          disabled={alTope}
          title={alTope ? `Solo se permiten ${maximo}` : textoAgregar}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-slate-300 bg-slate-50 py-2 text-xs font-medium text-brand-600 transition-colors hover:bg-brand-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-slate-50"
        >
          <Plus size={14} />
          {alTope ? `Máximo ${maximo}` : textoAgregar}
        </button>
      </div>
    </div>
  )
}
