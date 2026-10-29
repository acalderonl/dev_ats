/**
 * Simulación de cómo quedará el post en una red social profesional.
 *
 * Deliberadamente **genérica**: tipografía y aire de una red profesional, pero sin
 * nombre, sin logotipo y sin los colores exactos de ninguna marca. Se llama «Red
 * social» a propósito. La idea es ver si el post está bien armado, no imitar a nadie.
 *
 * Lo que se dibuja no lo inventa esta pantalla: el texto y los tres datos de la
 * tarjeta vienen de la misma función del servidor que arma lo que se publica. Una
 * simulación que reconstruyera el texto por su cuenta enseñaría algo *parecido*, y
 * "parecido" no sirve para decidir si el post está listo.
 */

import { Globe, MessageSquare, Repeat2, Send, ThumbsUp } from 'lucide-react'
import type { VistaPreviaDelPost } from '@/types'

/** Azul sobrio de red profesional, elegido para no ser el de ninguna marca concreta. */
const AZUL = '#1b64b8'

/** Lo que la red social recorta del texto antes del «…ver más». */
const CARACTERES_ANTES_DE_VER_MAS = 210

function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  return (partes[0][0] + (partes[1]?.[0] ?? '')).toUpperCase()
}

/** Pinta las etiquetas en azul, como hace cualquier red. El resto va tal cual. */
function ConEtiquetas({ texto }: { texto: string }) {
  return (
    <>
      {texto.split(/(#[\p{L}\p{N}_]+)/gu).map((trozo, i) =>
        trozo.startsWith('#') ? (
          <span key={i} style={{ color: AZUL }} className="font-medium">
            {trozo}
          </span>
        ) : (
          <span key={i}>{trozo}</span>
        ),
      )}
    </>
  )
}

export function SimulacionDeRedSocial({ previa }: { previa: VistaPreviaDelPost }) {
  const recortado = previa.cuerpo.length > CARACTERES_ANTES_DE_VER_MAS

  return (
    <div className="space-y-3">
      <p className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">
        Simulación. Así quedaría tu publicación; los colores y el nombre de la red son genéricos.
      </p>

      <article
        className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
        style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif' }}
      >
        <header className="flex items-start gap-3 p-4 pb-2">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
            style={{ backgroundColor: AZUL }}
            aria-hidden
          >
            {iniciales(previa.autor)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900">{previa.autor}</p>
            <p className="truncate text-xs text-slate-500">Academia Naval Almirante Illingworth</p>
            <p className="flex items-center gap-1 text-xs text-slate-400">
              Ahora · <Globe size={11} />
            </p>
          </div>
        </header>

        <div className="px-4 pb-3 text-sm leading-relaxed text-slate-800">
          <p className="whitespace-pre-wrap">
            <ConEtiquetas texto={previa.cuerpo} />
          </p>
          {recortado && (
            <p className="mt-1 text-xs text-slate-400">
              Se verá cortado con «…ver más» pasados unos {CARACTERES_ANTES_DE_VER_MAS} caracteres.
            </p>
          )}
        </div>

        {/* La tarjeta del enlace. Sale de lo que se le manda a la red: si falta la
            imagen aquí, también faltará allí. */}
        <div className="border-y border-slate-200 bg-slate-50">
          {previa.imagen_url ? (
            <img src={previa.imagen_url} alt="" className="max-h-72 w-full object-cover" />
          ) : (
            <div className="flex h-24 items-center justify-center border-b border-slate-200 bg-slate-100 text-xs text-slate-400">
              Sin imagen: la tarjeta saldrá solo con texto
            </div>
          )}
          <div className="px-4 py-3">
            <p className="line-clamp-2 text-sm font-semibold text-slate-900">{previa.tarjeta_titulo}</p>
            <p className="line-clamp-2 text-xs text-slate-600">{previa.tarjeta_descripcion}</p>
            <p className="mt-1 text-xs text-slate-400">{previa.tarjeta_dominio}</p>
          </div>
        </div>

        {/* Los botones son de adorno: están para que se vea el conjunto, no funcionan. */}
        <footer className="flex items-center justify-around px-2 py-1 text-xs font-medium text-slate-500">
          {[
            { icono: ThumbsUp, texto: 'Recomendar' },
            { icono: MessageSquare, texto: 'Comentar' },
            { icono: Repeat2, texto: 'Compartir' },
            { icono: Send, texto: 'Enviar' },
          ].map(({ icono: Icono, texto }) => (
            <span key={texto} className="flex items-center gap-1.5 rounded px-3 py-2">
              <Icono size={15} /> {texto}
            </span>
          ))}
        </footer>
      </article>
    </div>
  )
}
