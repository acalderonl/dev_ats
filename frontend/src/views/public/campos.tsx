/**
 * Los campos del formulario de postulación.
 *
 * Están aquí y no dentro de la vista porque el formulario repite las mismas cuatro
 * formas decenas de veces; tenerlas sueltas haría que un cambio de estilo o de
 * accesibilidad hubiera que repetirlo en cada aparición.
 */

import { useId } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { MESES, anios } from '@/lib/catalogosDelFormulario'

const CLASES_DE_CAMPO =
  'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-50 disabled:text-slate-400'

function Etiqueta({ texto, obligatorio, para }: { texto: string; obligatorio?: boolean; para: string }) {
  return (
    <label htmlFor={para} className="mb-1 block text-sm font-medium text-slate-700">
      {texto}
      {obligatorio && <span className="ml-0.5 text-red-500">*</span>}
    </label>
  )
}

export function Texto({
  etiqueta,
  valor,
  onChange,
  obligatorio,
  tipo = 'text',
  placeholder,
  ayuda,
  error,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  obligatorio?: boolean
  tipo?: 'text' | 'email' | 'tel' | 'url' | 'number'
  placeholder?: string
  ayuda?: string
  error?: string
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta texto={etiqueta} obligatorio={obligatorio} para={id} />
      <input
        id={id}
        type={tipo}
        value={valor}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={`${CLASES_DE_CAMPO} ${error ? 'border-red-400' : ''}`}
      />
      {error ? (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      ) : (
        ayuda && <p className="mt-1 text-xs text-slate-500">{ayuda}</p>
      )}
    </div>
  )
}

export function Selector({
  etiqueta,
  valor,
  onChange,
  opciones,
  obligatorio,
  error,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  opciones: readonly string[]
  obligatorio?: boolean
  error?: string
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta texto={etiqueta} obligatorio={obligatorio} para={id} />
      <select
        id={id}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        className={`${CLASES_DE_CAMPO} ${error ? 'border-red-400' : ''} ${valor ? '' : 'text-slate-400'}`}
      >
        <option value="">Seleccione una opción</option>
        {opciones.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

/**
 * Campo con sugerencias pero sin lista cerrada.
 *
 * Para país, institución, idioma y parecidos: se ofrece lo frecuente y se acepta
 * cualquier cosa. Un selector cerrado dejaría fuera a quien estudió donde no
 * previmos, y entonces el dato se pierde o se escribe en otro campo.
 */
export function Sugerido({
  etiqueta,
  valor,
  onChange,
  sugerencias,
  obligatorio,
  placeholder,
  error,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  sugerencias: readonly string[]
  obligatorio?: boolean
  placeholder?: string
  error?: string
}) {
  const id = useId()
  const listaId = `${id}-opciones`
  return (
    <div>
      <Etiqueta texto={etiqueta} obligatorio={obligatorio} para={id} />
      <input
        id={id}
        list={listaId}
        value={valor}
        placeholder={placeholder ?? 'Escribe o elige'}
        onChange={(e) => onChange(e.target.value)}
        className={`${CLASES_DE_CAMPO} ${error ? 'border-red-400' : ''}`}
      />
      <datalist id={listaId}>
        {sugerencias.map((s) => (
          <option key={s} value={s} />
        ))}
      </datalist>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}

export function Area({
  etiqueta,
  valor,
  onChange,
  maximo = 1000,
  filas = 4,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  maximo?: number
  filas?: number
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta texto={etiqueta} para={id} />
      <textarea
        id={id}
        value={valor}
        rows={filas}
        maxLength={maximo}
        onChange={(e) => onChange(e.target.value)}
        className={CLASES_DE_CAMPO}
      />
      <p className="mt-1 text-right text-xs text-slate-400">
        {valor.length}/{maximo}
      </p>
    </div>
  )
}

export function Casilla({
  etiqueta,
  valor,
  onChange,
}: {
  etiqueta: React.ReactNode
  valor: boolean
  onChange: (v: boolean) => void
}) {
  const id = useId()
  return (
    <div className="flex items-start gap-2">
      <input
        id={id}
        type="checkbox"
        checked={valor}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
      />
      <label htmlFor={id} className="text-sm text-slate-700">
        {etiqueta}
      </label>
    </div>
  )
}

/** Mes y año, que es como viene una fecha en un CV: casi nunca trae el día. */
export function MesYAnio({
  etiqueta,
  mes,
  anio,
  onChange,
  deshabilitado,
}: {
  etiqueta: string
  mes: number | null
  anio: number | null
  onChange: (mes: number | null, anio: number | null) => void
  deshabilitado?: boolean
}) {
  const id = useId()
  return (
    <div>
      <Etiqueta texto={etiqueta} para={id} />
      <div className="flex gap-2">
        <select
          id={id}
          value={mes ?? ''}
          disabled={deshabilitado}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null, anio)}
          className={`${CLASES_DE_CAMPO} ${mes ? '' : 'text-slate-400'}`}
        >
          <option value="">Mes</option>
          {MESES.map((m, i) => (
            <option key={m} value={i + 1}>
              {m}
            </option>
          ))}
        </select>
        <select
          value={anio ?? ''}
          disabled={deshabilitado}
          onChange={(e) => onChange(mes, e.target.value ? Number(e.target.value) : null)}
          className={`${CLASES_DE_CAMPO} ${anio ? '' : 'text-slate-400'}`}
        >
          <option value="">Año</option>
          {anios().map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

export function Seccion({
  titulo,
  descripcion,
  children,
}: {
  titulo: string
  descripcion?: string
  children: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      <div className="border-b border-slate-100 pb-2">
        <h3 className="text-sm font-semibold text-slate-800">{titulo}</h3>
        {descripcion && <p className="mt-0.5 text-xs text-slate-500">{descripcion}</p>}
      </div>
      {children}
    </section>
  )
}

/** Una fila repetible (una educación, un idioma, un trabajo) con su botón de quitar. */
export function Tarjeta({ children, onEliminar }: { children: React.ReactNode; onEliminar: () => void }) {
  return (
    <div className="space-y-4 rounded-xl border border-slate-200 p-4">
      {children}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onEliminar}
          className="flex items-center gap-1 text-xs font-medium text-red-600 hover:underline"
        >
          <Trash2 size={13} /> Eliminar
        </button>
      </div>
    </div>
  )
}

export function BotonAnadir({ texto, onClick }: { texto: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-1 text-sm font-medium text-brand-600 hover:underline"
    >
      <Plus size={15} /> {texto}
    </button>
  )
}
