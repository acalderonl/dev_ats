import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { competenciasService } from '@/services/competenciasService'
import { ApiError } from '@/lib/apiClient'
import type { Competencia, CompetenciaDelCargo, TipoCompetencia } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/** A partir de aquí dos textos se parecen lo bastante como para avisar antes de crear otro. */
const UMBRAL_AVISO = 0.55

/**
 * Lista de competencias de un cargo, con buscador que evita duplicados.
 *
 * Al escribir busca en lo que ya existe (coincidencia literal y por parecido) para que se
 * reutilice "Trabajo en equipo" en vez de crear "Trabajo en equipos". Solo si de verdad no
 * existe se ofrece crearla, y si hay algo muy parecido se avisa antes.
 */
export function SelectorCompetencias({
  tipo,
  etiqueta,
  placeholder,
  seleccionadas,
  onChange,
}: {
  tipo: TipoCompetencia
  etiqueta: string
  placeholder: string
  seleccionadas: CompetenciaDelCargo[]
  onChange: (competencias: CompetenciaDelCargo[]) => void
}) {
  const [texto, setTexto] = useState('')
  const [sugerencias, setSugerencias] = useState<Competencia[]>([])
  const [buscando, setBuscando] = useState(false)
  const [creando, setCreando] = useState(false)
  const contenedor = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!texto.trim()) {
      setSugerencias([])
      return
    }
    setBuscando(true)
    const temporizador = setTimeout(() => {
      competenciasService
        .buscar(tipo, texto)
        .then(setSugerencias)
        .catch((err) => toast.error(errorMessage(err)))
        .finally(() => setBuscando(false))
    }, 250)
    return () => clearTimeout(temporizador)
  }, [texto, tipo])

  const yaElegidas = new Set(seleccionadas.map((c) => c.competencia_id))
  const disponibles = sugerencias.filter((s) => !yaElegidas.has(s.id))
  const normalizado = texto.trim().toLowerCase()
  const hayExacta = sugerencias.some((s) => s.nombre.trim().toLowerCase() === normalizado)
  // El aviso mira TODAS las sugerencias, también las ya elegidas: avisar de que estás a punto
  // de crear algo casi idéntico a lo que ya tienes en la lista es justo el caso que importa.
  const parecida = hayExacta
    ? undefined
    : sugerencias.find((s) => (s.similitud ?? 0) >= UMBRAL_AVISO)
  const parecidaYaElegida = parecida ? yaElegidas.has(parecida.id) : false

  function agregar(competencia: Competencia) {
    onChange([
      ...seleccionadas,
      {
        competencia_id: competencia.id,
        nombre: competencia.nombre,
        tipo: competencia.tipo,
        requerido: true,
        deseado: false,
      },
    ])
    setTexto('')
    setSugerencias([])
  }

  async function crearYAgregar() {
    if (!texto.trim()) return
    // Con una parecida delante no se crea nada: el objetivo del buscador es que se
    // reutilice la que ya existe, no acabar con dos versiones de lo mismo.
    if (parecida) {
      toast.error(
        parecidaYaElegida
          ? `"${parecida.nombre}" ya está en la lista. No se pueden tener repetidos.`
          : `Ya existe "${parecida.nombre}". Elígela de la lista en vez de crear una repetida.`
      )
      return
    }
    setCreando(true)
    try {
      // Si ya existía escrita de otra forma, el backend devuelve la existente.
      const competencia = await competenciasService.crear(tipo, texto.trim())
      if (yaElegidas.has(competencia.id)) {
        toast.info(`"${competencia.nombre}" ya está en la lista`)
        setTexto('')
        return
      }
      agregar(competencia)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setCreando(false)
    }
  }

  /** Requerido y deseado se excluyen: marcar uno apaga el otro. Volver a pulsar deja ninguno. */
  function alternar(id: number, campo: 'requerido' | 'deseado') {
    onChange(
      seleccionadas.map((c) => {
        if (c.competencia_id !== id) return c
        const activando = !c[campo]
        return { ...c, requerido: false, deseado: false, [campo]: activando }
      })
    )
  }

  function quitar(id: number) {
    onChange(seleccionadas.filter((c) => c.competencia_id !== id))
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700">{etiqueta}</label>

      <div ref={contenedor} className="relative">
        <div className="flex gap-2">
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter') return
              e.preventDefault()
              if (hayExacta) {
                // La misma, escrita igual: si está libre se añade; si ya la tiene, se avisa.
                const exacta = disponibles.find((s) => s.nombre.trim().toLowerCase() === normalizado)
                if (exacta) agregar(exacta)
                else toast.error(`"${texto.trim()}" ya está en la lista. No se pueden tener repetidos.`)
                return
              }
              crearYAgregar()
            }}
            placeholder={placeholder}
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          {buscando && (
            <span className="flex items-center text-slate-300">
              <Loader2 size={16} className="animate-spin" />
            </span>
          )}
        </div>

        {texto.trim() && (
          <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
            {disponibles.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => agregar(s)}
                className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-brand-50"
              >
                <span className="min-w-0 truncate text-slate-700">{s.nombre}</span>
                <span className="shrink-0 text-xs text-slate-400">
                  {s.usos > 0 ? `en ${s.usos} cargo${s.usos === 1 ? '' : 's'}` : 'sin usar'}
                </span>
              </button>
            ))}

            {!hayExacta && (
              <button
                type="button"
                onClick={crearYAgregar}
                disabled={creando || Boolean(parecida)}
                title={parecida ? `Demasiado parecida a "${parecida.nombre}"` : undefined}
                className="flex w-full items-center gap-2 border-t border-slate-100 bg-slate-50 px-3 py-2 text-left text-sm font-medium text-brand-600 hover:bg-brand-50 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-slate-50"
              >
                {creando ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                Crear «{texto.trim()}»
              </button>
            )}

            {parecida && (
              <p className="flex items-start gap-1.5 border-t border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                <span>
                  {parecidaYaElegida ? (
                    <>
                      Ya tienes <strong>{parecida.nombre}</strong> en la lista. Crear esta sería
                      duplicarla.
                    </>
                  ) : (
                    <>
                      Ya existe <strong>{parecida.nombre}</strong>. Úsala en vez de crear una
                      parecida, para que no se dupliquen.
                    </>
                  )}
                </span>
              </p>
            )}
          </div>
        )}
      </div>

      {seleccionadas.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-400">
          Escribe arriba para buscar o crear.
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200">
          {seleccionadas.map((c) => (
            <div
              key={c.competencia_id}
              className="flex flex-wrap items-center gap-3 border-b border-slate-100 px-3 py-2 last:border-b-0"
            >
              <span className="min-w-0 flex-1 truncate text-sm text-slate-800">{c.nombre}</span>
              <label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={c.requerido}
                  onChange={() => alternar(c.competencia_id, 'requerido')}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                Requerido
              </label>
              <label className="flex shrink-0 cursor-pointer items-center gap-1.5 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={c.deseado}
                  onChange={() => alternar(c.competencia_id, 'deseado')}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                Deseado
              </label>
              <button
                type="button"
                onClick={() => quitar(c.competencia_id)}
                title="Quitar"
                className="shrink-0 rounded p-1 text-slate-300 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
