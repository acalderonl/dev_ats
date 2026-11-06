import { Settings2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Jornada } from '@/types'

/**
 * Primero la jornada, luego la hora de entrada; la de salida se calcula.
 *
 * La de salida queda editable a propósito: el cálculo cubre el caso normal, pero hay
 * horarios con pausa de almuerzo que no son entrada + horas. Se rellena sola y se
 * puede corregir.
 *
 * Las jornadas no están en el código: se administran en Configuración, porque cuántas
 * horas se trabajan cambia por país, contrato y puesto.
 */
export function sumarHoras(entrada: string, horas: number): string {
  const [h, m] = entrada.split(':').map(Number)
  const total = (h * 60 + m + Math.round(horas * 60)) % (24 * 60)
  const hh = String(Math.floor(total / 60)).padStart(2, '0')
  const mm = String(total % 60).padStart(2, '0')
  return `${hh}:${mm}`
}

export function SelectorDeHorario({
  jornadas,
  jornadaHoras,
  horaEntrada,
  horaSalida,
  onChange,
  puedeConfigurar,
}: {
  jornadas: Jornada[]
  jornadaHoras: string
  horaEntrada: string
  horaSalida: string
  onChange: (cambios: { jornadaHoras?: string; horaEntrada?: string; horaSalida?: string }) => void
  puedeConfigurar: boolean
}) {
  function elegirJornada(horas: string) {
    // Si ya había entrada, recalcular la salida con la jornada nueva.
    const salida = horas && horaEntrada ? sumarHoras(horaEntrada, Number(horas)) : horaSalida
    onChange({ jornadaHoras: horas, horaSalida: salida })
  }

  function elegirEntrada(entrada: string) {
    const salida = entrada && jornadaHoras ? sumarHoras(entrada, Number(jornadaHoras)) : horaSalida
    onChange({ horaEntrada: entrada, horaSalida: salida })
  }

  const activas = jornadas.filter((j) => j.activo)

  return (
    <div className="space-y-3">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-sm font-medium text-slate-700">Jornada</label>
          {puedeConfigurar && (
            <Link
              to="/configuracion"
              title="Administrar las jornadas"
              className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <Settings2 size={15} />
            </Link>
          )}
        </div>
        <select
          value={jornadaHoras}
          onChange={(e) => elegirJornada(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">Selecciona...</option>
          {activas.map((j) => (
            <option key={j.id} value={j.horas}>
              {j.nombre}
            </option>
          ))}
        </select>
        {activas.length === 0 && (
          <p className="mt-1 text-xs text-amber-600">
            No hay jornadas configuradas{puedeConfigurar ? '. Créalas en Configuración.' : '.'}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Hora de entrada</label>
          <input
            type="time"
            value={horaEntrada}
            onChange={(e) => elegirEntrada(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Hora de salida</label>
          <input
            type="time"
            value={horaSalida}
            onChange={(e) => onChange({ horaSalida: e.target.value })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>
      {jornadaHoras && horaEntrada && (
        <p className="text-xs text-slate-500">
          Calculada a partir de la jornada. Puedes corregirla si el horario tiene pausa.
        </p>
      )}
    </div>
  )
}
