import { useMemo } from 'react'
import { Check, Minus } from 'lucide-react'
import type { Permiso } from '@/types'

/** El nombre del módulo tal como aparece en el menú lateral. */
const NOMBRE_DEL_MODULO: Record<string, string> = {
  dashboard: 'Dashboard',
  cargos: 'Cargos',
  vacantes: 'Vacantes',
  pipeline: 'Pipeline',
  contactos: 'Contactos',
  evaluaciones: 'Evaluaciones',
  usuarios: 'Usuarios y Roles',
  configuracion: 'Configuración',
}

/**
 * Casillas de permisos agrupadas por módulo.
 *
 * `heredados` existe para el caso de un usuario: ahí lo que se marca no es el permiso
 * en bruto sino la **diferencia respecto a su rol**, y hay que poder ver de un vistazo
 * qué viene del rol y qué se le tocó a mano. En la pantalla de roles no se pasa, y
 * entonces las casillas son simplemente lo que el rol da.
 */
export function SelectorDePermisos({
  catalogo,
  seleccionados,
  heredados,
  onToggle,
  deshabilitado,
}: {
  catalogo: Permiso[]
  seleccionados: Set<string>
  heredados?: Set<string>
  onToggle: (clave: string, marcado: boolean) => void
  deshabilitado?: boolean
}) {
  const porModulo = useMemo(() => {
    const mapa = new Map<string, Permiso[]>()
    for (const permiso of catalogo) {
      const lista = mapa.get(permiso.modulo) ?? []
      lista.push(permiso)
      mapa.set(permiso.modulo, lista)
    }
    return [...mapa.entries()]
  }, [catalogo])

  function alternarModulo(permisos: Permiso[]) {
    const todosPuestos = permisos.every((p) => seleccionados.has(p.clave))
    permisos.forEach((p) => onToggle(p.clave, !todosPuestos))
  }

  return (
    <div className="space-y-4">
      {porModulo.map(([modulo, permisos]) => {
        const marcados = permisos.filter((p) => seleccionados.has(p.clave)).length
        return (
          <div key={modulo} className="rounded-lg border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-3 py-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-800">
                  {NOMBRE_DEL_MODULO[modulo] ?? modulo}
                </span>
                <span className="text-xs text-slate-500">
                  {marcados} de {permisos.length}
                </span>
              </div>
              <button
                type="button"
                onClick={() => alternarModulo(permisos)}
                disabled={deshabilitado}
                className="text-xs font-medium text-brand-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-400 disabled:no-underline"
              >
                {marcados === permisos.length ? 'Quitar todo' : 'Marcar todo'}
              </button>
            </div>

            <div className="divide-y divide-slate-50">
              {permisos.map((permiso) => {
                const marcado = seleccionados.has(permiso.clave)
                const vieneDelRol = heredados?.has(permiso.clave)
                // Solo interesa señalar la diferencia cuando la hay.
                const esAjuste = heredados !== undefined && marcado !== Boolean(vieneDelRol)
                return (
                  <label
                    key={permiso.clave}
                    className={`flex cursor-pointer items-center gap-3 px-3 py-2 hover:bg-slate-50 ${
                      deshabilitado ? 'cursor-not-allowed opacity-60' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={marcado}
                      disabled={deshabilitado}
                      onChange={(e) => onToggle(permiso.clave, e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="flex-1 text-sm text-slate-700">{permiso.etiqueta}</span>
                    {esAjuste && (
                      <span
                        className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium ${
                          marcado ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                        }`}
                        title={
                          marcado
                            ? 'Se le concedió aunque su rol no lo trae'
                            : 'Se le quitó aunque su rol sí lo trae'
                        }
                      >
                        {marcado ? <Check size={11} /> : <Minus size={11} />}
                        {marcado ? 'añadido' : 'quitado'}
                      </span>
                    )}
                  </label>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
