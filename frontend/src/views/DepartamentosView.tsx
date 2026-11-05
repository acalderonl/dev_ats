/**
 * Departamentos: la unidad organizativa a la que pertenecen los cargos.
 *
 * Se desactivan, no se borran, como todo lo que tiene historia detrás. Al desactivar
 * uno, sus cargos pasan a «Sin asignar»; la confirmación lo dice con el número, para
 * que nadie desactive un departamento sin saber qué mueve.
 */

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Building2, Loader2, Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { Modal } from '@/components/common/Modal'
import { ApiError } from '@/lib/apiClient'
import { huboCambios } from '@/lib/formDirty'
import { departamentosService } from '@/services/departamentosService'
import type { Departamento } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

const FORM_VACIO = { nombre: '', descripcion: '' }

export function DepartamentosView() {
  const [departamentos, setDepartamentos] = useState<Departamento[]>([])
  const [cargando, setCargando] = useState(true)
  const [pestana, setPestana] = useState<'activos' | 'inactivos'>('activos')

  const [modalAbierto, setModalAbierto] = useState(false)
  const [enEdicion, setEnEdicion] = useState<Departamento | null>(null)
  const [form, setForm] = useState(FORM_VACIO)
  // Lo que había al abrir el modal, para saber si hay algo que perder al cerrarlo.
  const [formInicial, setFormInicial] = useState(FORM_VACIO)
  const [guardando, setGuardando] = useState(false)

  const [aConfirmar, setAConfirmar] = useState<Departamento | null>(null)
  const [cambiando, setCambiando] = useState(false)

  const activos = useMemo(() => departamentos.filter((d) => d.activo), [departamentos])
  const inactivos = useMemo(() => departamentos.filter((d) => !d.activo), [departamentos])
  const visibles = pestana === 'activos' ? activos : inactivos

  async function cargar() {
    try {
      setDepartamentos(await departamentosService.list())
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar()
  }, [])

  function abrirNuevo() {
    setEnEdicion(null)
    setForm(FORM_VACIO)
    setFormInicial(FORM_VACIO)
    setModalAbierto(true)
  }

  function abrirEdicion(d: Departamento) {
    const datos = { nombre: d.nombre, descripcion: d.descripcion ?? '' }
    setEnEdicion(d)
    setForm(datos)
    setFormInicial(datos)
    setModalAbierto(true)
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault()
    if (!form.nombre.trim()) return toast.error('El nombre es obligatorio')
    setGuardando(true)
    try {
      const datos = { nombre: form.nombre.trim(), descripcion: form.descripcion.trim() || null }
      if (enEdicion) {
        await departamentosService.update(enEdicion.id, datos)
        toast.success('Departamento actualizado')
      } else {
        await departamentosService.create(datos)
        toast.success(`Departamento «${datos.nombre}» creado`)
      }
      setModalAbierto(false)
      await cargar()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function confirmarCambio() {
    if (!aConfirmar) return
    setCambiando(true)
    try {
      await departamentosService.toggleActivo(aConfirmar.id)
      toast.success(aConfirmar.activo ? 'Departamento desactivado' : 'Departamento reactivado')
      setAConfirmar(null)
      await cargar()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setCambiando(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Departamentos no tiene entrada propia en el menú lateral: se entra desde un
          botón en Cargos, así que hace falta uno explícito para volver. */}
      <Link
        to="/cargos"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft size={15} /> Volver a Cargos
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Departamentos</h1>
          <p className="text-sm text-slate-500">
            Las unidades de la institución. Cada cargo pertenece a una, y esta pantalla se
            organiza por ellas.
          </p>
        </div>
        {pestana === 'activos' && (
          <button
            onClick={abrirNuevo}
            className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <Plus size={16} /> Nuevo departamento
          </button>
        )}
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {(
          [
            ['activos', `Activos (${activos.length})`],
            ['inactivos', `Inactivos (${inactivos.length})`],
          ] as const
        ).map(([valor, etiqueta]) => (
          <button
            key={valor}
            onClick={() => setPestana(valor)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              pestana === valor
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {etiqueta}
          </button>
        ))}
      </div>

      {cargando ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : visibles.length === 0 ? (
        <Card className="p-10">
          <p className="text-center text-sm text-slate-500">
            {pestana === 'activos'
              ? 'No hay departamentos activos.'
              : 'No hay departamentos inactivos. Los que desactives aparecerán aquí.'}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visibles.map((d) => (
            <Card key={d.id} className="flex flex-col justify-between p-4">
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="flex items-center gap-2 font-medium text-slate-900">
                    <Building2 size={16} className="shrink-0 text-slate-400" />
                    {d.nombre}
                  </h3>
                  {d.es_sistema ? (
                    <Badge tone="slate">Del sistema</Badge>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setAConfirmar(d)}
                      title={d.activo ? 'Pulsa para desactivar' : 'Pulsa para reactivar'}
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                        d.activo
                          ? 'bg-green-50 text-green-700 hover:bg-green-100'
                          : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                      }`}
                    >
                      {d.activo ? 'Activo' : 'Inactivo'}
                    </button>
                  )}
                </div>
                {d.descripcion && <p className="mt-2 text-sm text-slate-600">{d.descripcion}</p>}
                <p className="mt-3 text-xs text-slate-500">
                  {d.cargos === 1 ? '1 cargo' : `${d.cargos} cargos`}
                </p>
              </div>
              {!d.es_sistema && (
                <div className="mt-4 flex justify-end border-t border-slate-100 pt-3">
                  <button
                    type="button"
                    onClick={() => abrirEdicion(d)}
                    className="flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-slate-900"
                  >
                    <Pencil size={13} /> Editar
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={modalAbierto}
        onClose={() => setModalAbierto(false)}
        title={enEdicion ? `Editar: ${enEdicion.nombre}` : 'Nuevo departamento'}
        confirmarCierre={huboCambios(form, formInicial) && 'Se perderá lo que hayas escrito.'}
      >
        <form onSubmit={guardar} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Nombre <span className="text-red-500">*</span>
            </label>
            <input
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              maxLength={120}
              autoFocus
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Descripción</label>
            <textarea
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setModalAbierto(false)}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando}
              className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {guardando && <Loader2 size={15} className="animate-spin" />}
              {enEdicion ? 'Guardar cambios' : 'Crear'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={aConfirmar !== null}
        onClose={() => setAConfirmar(null)}
        title={aConfirmar?.activo ? '¿Desactivar este departamento?' : '¿Reactivar este departamento?'}
      >
        {aConfirmar && (
          <div className="space-y-4">
            <p className="text-sm text-slate-700">
              <strong>{aConfirmar.nombre}</strong>
              {aConfirmar.activo ? (
                aConfirmar.cargos > 0 ? (
                  <>
                    {' '}
                    tiene {aConfirmar.cargos === 1 ? 'un cargo' : `${aConfirmar.cargos} cargos`}. Al
                    desactivarlo, {aConfirmar.cargos === 1 ? 'pasa' : 'pasan'} a{' '}
                    <strong>«Sin asignar»</strong>, para que ningún cargo quede sin sitio. Podrás
                    reasignarlos desde Cargos.
                  </>
                ) : (
                  <> no tiene cargos. Dejará de ofrecerse al crear un cargo, pero no se borra.</>
                )
              ) : (
                <> volverá a ofrecerse al crear o editar un cargo.</>
              )}
            </p>
            <p className="text-xs text-slate-500">
              No se elimina: un departamento puede tener historia detrás y borrarlo la dejaría sin
              contexto.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setAConfirmar(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmarCambio}
                disabled={cambiando}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
                  aConfirmar.activo ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-600 hover:bg-brand-700'
                }`}
              >
                {cambiando && <Loader2 size={15} className="animate-spin" />}
                {aConfirmar.activo ? 'Desactivar' : 'Reactivar'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
