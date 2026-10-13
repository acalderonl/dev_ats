import { X } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'

export function Modal({
  open,
  onClose,
  title,
  children,
  wide,
  confirmarCierre,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  wide?: boolean
  /**
   * Texto de la pregunta de seguridad. Si se pasa, cerrar —con la X o haciendo clic
   * fuera— pregunta antes en vez de cerrar directamente.
   *
   * Es opcional a propósito: un modal que ya es él mismo una confirmación no debe
   * pedir confirmación para cerrarse.
   */
  confirmarCierre?: string
}) {
  const [preguntando, setPreguntando] = useState(false)

  // Si el modal se cierra por otra vía (al guardar, por ejemplo), la pregunta no
  // puede quedar en pie esperando a la próxima apertura.
  useEffect(() => {
    if (!open) setPreguntando(false)
  }, [open])

  if (!open) return null

  const intentarCerrar = () => {
    if (confirmarCierre) setPreguntando(true)
    else onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0" onClick={intentarCerrar} />
      <div
        className={`relative z-10 flex max-h-[90vh] w-full ${wide ? 'max-w-2xl' : 'max-w-md'} flex-col overflow-hidden rounded-xl bg-white shadow-xl`}
      >
        {/* La cabecera queda fuera del área que hace scroll: el título y la X no se mueven. */}
        <div className="flex shrink-0 items-center justify-between border-b border-slate-100 bg-white px-5 py-4">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <button
            type="button"
            onClick={intentarCerrar}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>
        <div className="overflow-y-auto p-5">{children}</div>

        {preguntando && (
          <div className="absolute inset-0 z-20 flex items-center justify-center p-5">
            <div className="w-full max-w-sm space-y-5 rounded-xl bg-white p-5 shadow-xl">
              <div>
                <h3 className="text-base font-semibold text-slate-900">¿Cerrar sin guardar?</h3>
                <p className="mt-2 text-sm text-slate-600">{confirmarCierre}</p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPreguntando(false)}
                  className="flex-1 rounded-lg border border-slate-300 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPreguntando(false)
                    onClose()
                  }}
                  className="flex-1 rounded-lg bg-red-600 py-2.5 text-sm font-medium text-white hover:bg-red-700"
                >
                  Sí, cerrar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
