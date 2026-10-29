import { useEffect, useState } from 'react'
import { Check, Pencil, Plus, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'
import { Modal } from '@/components/common/Modal'
import { Badge } from '@/components/common/Badge'
import { useDataStore } from '@/store/dataStore'
import { ApiError } from '@/lib/apiClient'
import type { CatalogoTipo } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/**
 * CRUD de un catálogo. Lo abre el engranaje que hay junto a cada selector del
 * formulario de cargo; sirve igual para cualquier catálogo porque todos tienen
 * la misma forma (id, nombre, activo).
 */
export function GestionCatalogoModal({
  tipo,
  titulo,
  abierto,
  onClose,
  onItemCreado,
}: {
  tipo: CatalogoTipo
  titulo: string
  abierto: boolean
  onClose: () => void
  /** Permite al formulario seleccionar automáticamente lo que se acaba de crear. */
  onItemCreado?: (id: number) => void
}) {
  const { catalogos, fetchCatalogo, createCatalogoItem, updateCatalogoItem, deleteCatalogoItem } =
    useDataStore()
  const items = catalogos[tipo] ?? []

  const [nuevo, setNuevo] = useState('')
  const [editandoId, setEditandoId] = useState<number | null>(null)
  const [editandoNombre, setEditandoNombre] = useState('')

  useEffect(() => {
    if (abierto) fetchCatalogo(tipo).catch((err) => toast.error(errorMessage(err)))
  }, [abierto, tipo, fetchCatalogo])

  async function handleCrear(e: React.FormEvent) {
    e.preventDefault()
    if (!nuevo.trim()) return
    try {
      const item = await createCatalogoItem(tipo, nuevo.trim())
      setNuevo('')
      onItemCreado?.(item.id)
      toast.success(`"${item.nombre}" agregado`)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleGuardarNombre(id: number) {
    if (!editandoNombre.trim()) return
    try {
      await updateCatalogoItem(tipo, id, { nombre: editandoNombre.trim() })
      setEditandoId(null)
      toast.success('Nombre actualizado')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleToggleActivo(id: number, activo: boolean) {
    try {
      await updateCatalogoItem(tipo, id, { activo: !activo })
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function handleEliminar(id: number, nombre: string) {
    try {
      await deleteCatalogoItem(tipo, id)
      toast.success(`"${nombre}" eliminado`)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <Modal open={abierto} onClose={onClose} title={`Gestionar ${titulo}`}>
      <div className="space-y-4">
        <form onSubmit={handleCrear} className="flex gap-2">
          <input
            value={nuevo}
            onChange={(e) => setNuevo(e.target.value)}
            placeholder={`Agregar ${titulo.toLowerCase().replace(/s$/, '')}...`}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button
            type="submit"
            disabled={!nuevo.trim()}
            className="flex shrink-0 items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-40"
          >
            <Plus size={15} /> Agregar
          </button>
        </form>

        <div className="max-h-80 space-y-1.5 overflow-y-auto">
          {items.length === 0 && (
            <p className="py-6 text-center text-sm text-slate-400">
              Todavía no hay elementos. Agrega el primero arriba.
            </p>
          )}

          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-2 rounded-lg border border-slate-100 px-3 py-2"
            >
              {editandoId === item.id ? (
                <>
                  <input
                    autoFocus
                    value={editandoNombre}
                    onChange={(e) => setEditandoNombre(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleGuardarNombre(item.id)
                      if (e.key === 'Escape') setEditandoId(null)
                    }}
                    className="min-w-0 flex-1 rounded border border-brand-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                  <button
                    onClick={() => handleGuardarNombre(item.id)}
                    title="Guardar"
                    className="rounded p-1.5 text-emerald-600 hover:bg-emerald-50"
                  >
                    <Check size={15} />
                  </button>
                  <button
                    onClick={() => setEditandoId(null)}
                    title="Cancelar"
                    className="rounded p-1.5 text-slate-400 hover:bg-slate-100"
                  >
                    <X size={15} />
                  </button>
                </>
              ) : (
                <>
                  <span
                    className={`min-w-0 flex-1 truncate text-sm ${
                      item.activo ? 'text-slate-800' : 'text-slate-400 line-through'
                    }`}
                  >
                    {item.nombre}
                  </span>
                  {item.en_uso && <Badge tone="blue">En uso</Badge>}
                  <button
                    onClick={() => {
                      setEditandoId(item.id)
                      setEditandoNombre(item.nombre)
                    }}
                    title="Renombrar"
                    className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => handleToggleActivo(item.id, item.activo)}
                    className="rounded border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50"
                  >
                    {item.activo ? 'Desactivar' : 'Activar'}
                  </button>
                  <button
                    onClick={() => handleEliminar(item.id, item.nombre)}
                    disabled={item.en_uso}
                    title={
                      item.en_uso
                        ? 'No se puede eliminar: hay cargos que lo usan. Desactívalo para ocultarlo del selector.'
                        : 'Eliminar'
                    }
                    className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        <p className="border-t border-slate-100 pt-3 text-xs text-slate-400">
          Lo que esté <strong>en uso</strong> no se puede eliminar. Desactívalo si solo quieres que deje
          de aparecer en el selector: los cargos que ya lo tienen lo conservan.
        </p>
      </div>
    </Modal>
  )
}
