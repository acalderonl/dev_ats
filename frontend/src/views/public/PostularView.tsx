/**
 * Formulario de postulación en tres pasos.
 *
 * Los campos son los del esquema que entregó la institución
 * (`docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx`), y son también los que
 * la lectura del CV intenta extraer: el paso 1 rellena, los pasos 2 y 3 se revisan.
 * Por eso se guarda `origen_datos`, para saber después si una ficha la escribió una
 * persona o la rellenó la extracción sin que nadie la mirara.
 */

import { useEffect, useRef, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileCheck2,
  Loader2,
  Plus,
  Trash2,
  UploadCloud,
} from 'lucide-react'
import { toast } from 'sonner'
import { publicService } from '@/services/publicService'
import { ApiError } from '@/lib/apiClient'
import type {
  EducacionItem,
  ExperienciaItem,
  IdiomaItem,
  RedSocial,
  VacantePublica,
} from '@/types'
import {
  AREAS_DE_ESTUDIO_SUGERIDAS,
  AREAS_DE_TRABAJO_SUGERIDAS,
  ESTADOS_DE_ESTUDIO,
  GENEROS,
  IDIOMAS_SUGERIDOS,
  INDUSTRIAS_SUGERIDAS,
  JERARQUIAS,
  MESES,
  NIVELES_DE_ESTUDIO,
  NIVELES_DE_IDIOMA,
  PAISES_SUGERIDOS,
  PROVINCIAS_DE_ECUADOR,
  TIPOS_DE_DOCUMENTO,
  TIPOS_DE_TELEFONO,
  anios,
} from '@/lib/catalogosDelFormulario'
import {
  Area,
  BotonAnadir,
  Casilla,
  MesYAnio,
  Seccion,
  Selector,
  Sugerido,
  Tarjeta,
  Texto,
} from './campos'

type Paso = 'personales' | 'adicional' | 'listo'

const PASOS: { clave: Paso; titulo: string }[] = [
  { clave: 'personales', titulo: 'Datos personales' },
  { clave: 'adicional', titulo: 'Información adicional' },
]

interface Ficha {
  foto_url: string | null
  nombres: string
  apellidos: string
  email: string
  confirmarEmail: string
  tipo_documento: string
  cedula: string
  telefono_codigo_pais: string
  telefono: string
  telefono_tipo: string
  genero: string
  nacionalidad: string
  pais_residencia: string
  provincia: string
  localidad: string
  nacimientoDia: string
  nacimientoMes: string
  nacimientoAnio: string

  educacion: EducacionItem[]
  estudios_secundarios_completos: boolean | null
  idiomas: IdiomaItem[]
  experiencia: ExperienciaItem[]
  linkedin_url: string
  otras_redes: RedSocial[]
  cv_documento_url: string | null
  expectativas: string
  acepta_privacidad: boolean
}

const FICHA_VACIA: Ficha = {
  foto_url: null,
  nombres: '',
  apellidos: '',
  email: '',
  confirmarEmail: '',
  tipo_documento: '',
  cedula: '',
  telefono_codigo_pais: '+593',
  telefono: '',
  telefono_tipo: '',
  genero: '',
  nacionalidad: '',
  pais_residencia: '',
  provincia: '',
  localidad: '',
  nacimientoDia: '',
  nacimientoMes: '',
  nacimientoAnio: '',
  educacion: [],
  estudios_secundarios_completos: null,
  idiomas: [],
  experiencia: [],
  linkedin_url: '',
  otras_redes: [],
  cv_documento_url: null,
  expectativas: '',
  acepta_privacidad: false,
}

const EDUCACION_VACIA: EducacionItem = {
  titulo: null,
  pais: null,
  institucion: null,
  area_estudio: null,
  nivel_estudio: null,
  estado_estudio: null,
  inicio_mes: null,
  inicio_anio: null,
  actualmente: false,
  fin_mes: null,
  fin_anio: null,
  descripcion: null,
}

const IDIOMA_VACIO: IdiomaItem = { idioma: '', nivel_escrito: null, nivel_oral: null }

const EXPERIENCIA_VACIA: ExperienciaItem = {
  puesto: null,
  jerarquia: null,
  empresa: null,
  pais: null,
  industria: null,
  area_trabajo: null,
  subarea_trabajo: null,
  inicio_mes: null,
  inicio_anio: null,
  actualmente: false,
  fin_mes: null,
  fin_anio: null,
  descripcion: null,
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/** Texto para la caja; el modelo guarda `null` cuando no hay dato. */
const t = (v: string | null) => v ?? ''

/** Años para el selector de nacimiento: de hoy hacia atrás, nadie nace en el futuro. */
const ANIOS_DE_NACIMIENTO = anios(1940, 0)

export function PostularView() {
  const { slug } = useParams<{ slug: string }>()
  const [vacante, setVacante] = useState<VacantePublica | null>(null)
  const [expirada, setExpirada] = useState(false)
  const [noEncontrada, setNoEncontrada] = useState(false)
  const [cargandoVacante, setCargandoVacante] = useState(true)

  const [paso, setPaso] = useState<Paso>('personales')
  const [subiendoFoto, setSubiendoFoto] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [ficha, setFicha] = useState<Ficha>(FICHA_VACIA)
  const [respuestas, setRespuestas] = useState<Record<string, string>>({})
  const [errores, setErrores] = useState<Record<string, string>>({})
  const [nombreDelCv, setNombreDelCv] = useState<string | null>(null)

  // La foto se enseña desde el archivo que la persona acaba de elegir: la URL que
  // devuelve el servidor es privada y no se abre sin sesión, y así tampoco se espera
  // a una ida y vuelta para ver algo.
  const [fotoPreview, setFotoPreview] = useState<string | null>(null)
  const previaAnterior = useRef<string | null>(null)

  useEffect(() => {
    if (!slug) return
    publicService
      .getVacante(slug)
      .then(setVacante)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 410) setExpirada(true)
        else if (err instanceof ApiError && err.status === 404) setNoEncontrada(true)
        else toast.error(errorMessage(err))
      })
      .finally(() => setCargandoVacante(false))
  }, [slug])

  // Una URL de objeto ocupa memoria hasta que se revoca; sin esto, cambiar de foto
  // varias veces las va dejando colgadas.
  useEffect(() => {
    return () => {
      if (previaAnterior.current) URL.revokeObjectURL(previaAnterior.current)
    }
  }, [])

  function cambiar<K extends keyof Ficha>(campo: K, valor: Ficha[K]) {
    setFicha((f) => ({ ...f, [campo]: valor }))
    setErrores((e) => (e[campo as string] ? { ...e, [campo as string]: '' } : e))
  }

  function cambiarFila<T>(campo: 'educacion' | 'idiomas' | 'experiencia', indice: number, parcial: Partial<T>) {
    setFicha((f) => {
      const lista = [...(f[campo] as unknown as T[])]
      lista[indice] = { ...lista[indice], ...parcial }
      return { ...f, [campo]: lista }
    })
  }

  function quitarFila(campo: 'educacion' | 'idiomas' | 'experiencia' | 'otras_redes', indice: number) {
    setFicha((f) => ({ ...f, [campo]: (f[campo] as unknown[]).filter((_, i) => i !== indice) }))
  }

  // --------------------------------------------- Archivos que sube el candidato

  async function adjuntarCv(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0]
    if (!archivo) return
    try {
      const { url } = await publicService.subirCv(archivo)
      cambiar('cv_documento_url', url)
      setNombreDelCv(archivo.name)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      e.target.value = ''
    }
  }

  async function subirFoto(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0]
    if (!archivo) return
    setSubiendoFoto(true)
    try {
      const { url } = await publicService.subirFoto(archivo)
      cambiar('foto_url', url)
      if (previaAnterior.current) URL.revokeObjectURL(previaAnterior.current)
      const previa = URL.createObjectURL(archivo)
      previaAnterior.current = previa
      setFotoPreview(previa)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSubiendoFoto(false)
      e.target.value = ''
    }
  }

  // --------------------------------------------------------------- Validación

  function validarPersonales(): boolean {
    const faltan: Record<string, string> = {}
    const obligatorios: [keyof Ficha, string][] = [
      ['nombres', 'Nombre'],
      ['apellidos', 'Apellido'],
      ['email', 'Email'],
      ['tipo_documento', 'Tipo de documento'],
      ['cedula', 'N.º de documento'],
      ['telefono', 'Teléfono'],
      ['telefono_tipo', 'Tipo de teléfono'],
      ['genero', 'Género'],
      ['nacionalidad', 'Nacionalidad'],
      ['pais_residencia', 'País de residencia'],
      ['provincia', 'Provincia'],
      ['localidad', 'Localidad'],
    ]
    for (const [campo, nombre] of obligatorios) {
      if (!String(ficha[campo] ?? '').trim()) faltan[campo] = `${nombre} es obligatorio`
    }
    if (ficha.email && ficha.confirmarEmail !== ficha.email) {
      faltan.confirmarEmail = 'Los dos correos no coinciden'
    }
    if (!ficha.nacimientoDia || !ficha.nacimientoMes || !ficha.nacimientoAnio) {
      faltan.nacimiento = 'La fecha de nacimiento es obligatoria'
    }
    setErrores(faltan)
    if (Object.keys(faltan).length) toast.error('Faltan datos obligatorios por completar.')
    return Object.keys(faltan).length === 0
  }

  function fechaDeNacimiento(): string | null {
    if (!ficha.nacimientoDia || !ficha.nacimientoMes || !ficha.nacimientoAnio) return null
    const mes = ficha.nacimientoMes.padStart(2, '0')
    const dia = ficha.nacimientoDia.padStart(2, '0')
    return `${ficha.nacimientoAnio}-${mes}-${dia}`
  }

  function edadCumplida(): number | null {
    const fecha = fechaDeNacimiento()
    if (!fecha) return null
    const nacimiento = new Date(fecha)
    const hoy = new Date()
    let edad = hoy.getFullYear() - nacimiento.getFullYear()
    const mesesDeDiferencia = hoy.getMonth() - nacimiento.getMonth()
    // Si aún no llegó su cumpleaños este año, todavía tiene un año menos.
    if (mesesDeDiferencia < 0 || (mesesDeDiferencia === 0 && hoy.getDate() < nacimiento.getDate())) edad--
    return edad
  }

  async function enviar() {
    if (!slug) return
    if (!ficha.acepta_privacidad) {
      toast.error('Debes aceptar la política de privacidad para enviar tu postulación.')
      return
    }
    setEnviando(true)
    try {
      await publicService.postular(slug, {
        nombres: ficha.nombres.trim(),
        apellidos: ficha.apellidos.trim(),
        cedula: ficha.cedula.trim(),
        email: ficha.email.trim(),
        tipo_documento: ficha.tipo_documento || null,
        fecha_nacimiento: fechaDeNacimiento(),
        genero: ficha.genero || null,
        nacionalidad: ficha.nacionalidad || null,
        foto_url: ficha.foto_url,
        telefono_codigo_pais: ficha.telefono_codigo_pais || null,
        telefono: ficha.telefono || null,
        telefono_tipo: ficha.telefono_tipo || null,
        pais_residencia: ficha.pais_residencia || null,
        provincia: ficha.provincia || null,
        localidad: ficha.localidad || null,
        estudios_secundarios_completos: ficha.estudios_secundarios_completos,
        linkedin_url: ficha.linkedin_url || null,
        otras_redes: ficha.otras_redes.filter((r) => r.red && r.url),
        expectativas: ficha.expectativas || null,
        cv_documento_url: ficha.cv_documento_url,
        edad: edadCumplida(),
        educacion: ficha.educacion,
        idiomas: ficha.idiomas.filter((i) => i.idioma.trim()),
        experiencia: ficha.experiencia,
        respuestas_filtro: respuestas,
        origen: 'Directo',
        // Siempre 'manual': lo que llega por aquí lo escribió una persona. El robot de
        // ETL marcará 'cv' en las fichas que cree él.
        origen_datos: 'manual',
        acepta_privacidad: true,
      })
      setPaso('listo')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setEnviando(false)
    }
  }

  // ------------------------------------------------------------------ Pintado

  if (expirada) return <Navigate to="/vacante-expirada" replace />

  if (cargandoVacante) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="animate-spin text-slate-400" size={28} />
      </div>
    )
  }

  if (noEncontrada || !vacante) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 text-center">
        <p className="text-sm text-slate-500">Vacante no encontrada.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 sm:py-12">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6 text-center">
          <img src="/escudo-anai.svg" alt="Escudo de la ANAI" className="mx-auto mb-3 h-16 w-auto" />
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-escudo">
            Academia Naval Almirante Illingworth
          </p>
          <h1 className="text-lg font-semibold text-slate-900">{vacante.titulo}</h1>
          <p className="text-sm text-slate-500">
            {vacante.cargo_nombre} · Vence el {new Date(vacante.fecha_limite).toLocaleDateString('es-EC')}
          </p>
        </header>

        {paso !== 'listo' && (
          <nav className="mb-6 flex items-center justify-center gap-3 text-xs sm:gap-6">
            {PASOS.map((p, i) => {
              const activo = p.clave === paso
              const hecho = PASOS.findIndex((x) => x.clave === paso) > i
              return (
                <div key={p.clave} className="flex items-center gap-2">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full border text-[11px] ${
                      activo
                        ? 'border-brand-600 bg-brand-600 text-white'
                        : hecho
                          ? 'border-brand-600 text-brand-600'
                          : 'border-slate-300 text-slate-400'
                    }`}
                  >
                    {i + 1}
                  </span>
                  <span className={activo ? 'font-medium text-brand-700' : 'text-slate-400'}>{p.titulo}</span>
                </div>
              )
            })}
          </nav>
        )}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          {paso === 'personales' && (
            <div className="space-y-6">
              <p className="text-sm text-slate-500">{vacante.descripcion}</p>

              <div className="flex justify-end">
                <p className="text-xs text-slate-400">
                  Campos obligatorios <span className="text-red-500">*</span>
                </p>
              </div>

              <div className="flex flex-col gap-6 sm:flex-row">
                <div className="shrink-0 text-center">
                  <p className="mb-2 text-sm font-medium text-slate-700">Foto</p>
                  <label className="relative inline-block cursor-pointer">
                    <input type="file" accept="image/*" className="hidden" onChange={subirFoto} />
                    <span className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-full border-2 border-dashed border-slate-300 bg-slate-50">
                      {subiendoFoto ? (
                        <Loader2 className="animate-spin text-brand-600" size={22} />
                      ) : fotoPreview ? (
                        <img src={fotoPreview} alt="Tu foto" className="h-full w-full object-cover" />
                      ) : (
                        <UploadCloud className="text-slate-300" size={26} />
                      )}
                    </span>
                    <span className="absolute bottom-1 right-1 flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white shadow">
                      <Plus size={15} />
                    </span>
                  </label>
                </div>

                <div className="grid flex-1 gap-4 sm:grid-cols-2">
                  <Texto
                    etiqueta="Nombre"
                    obligatorio
                    valor={ficha.nombres}
                    onChange={(v) => cambiar('nombres', v)}
                    error={errores.nombres}
                  />
                  <Texto
                    etiqueta="Apellido"
                    obligatorio
                    valor={ficha.apellidos}
                    onChange={(v) => cambiar('apellidos', v)}
                    error={errores.apellidos}
                  />
                  <Texto
                    etiqueta="Email"
                    obligatorio
                    tipo="email"
                    valor={ficha.email}
                    onChange={(v) => cambiar('email', v)}
                    error={errores.email}
                  />
                  <Texto
                    etiqueta="Confirmar email"
                    obligatorio
                    tipo="email"
                    valor={ficha.confirmarEmail}
                    onChange={(v) => cambiar('confirmarEmail', v)}
                    error={errores.confirmarEmail}
                  />
                  <Selector
                    etiqueta="Tipo de documento"
                    obligatorio
                    valor={ficha.tipo_documento}
                    onChange={(v) => cambiar('tipo_documento', v)}
                    opciones={TIPOS_DE_DOCUMENTO}
                    error={errores.tipo_documento}
                  />
                  <Texto
                    etiqueta="N.º de documento"
                    obligatorio
                    valor={ficha.cedula}
                    onChange={(v) => cambiar('cedula', v)}
                    error={errores.cedula}
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="mb-1 block text-sm font-medium text-slate-700">
                    Teléfono<span className="ml-0.5 text-red-500">*</span>
                  </p>
                  <div className="flex gap-2">
                    <input
                      value={ficha.telefono_codigo_pais}
                      onChange={(e) => cambiar('telefono_codigo_pais', e.target.value)}
                      className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      aria-label="Código de país"
                    />
                    <input
                      value={ficha.telefono}
                      onChange={(e) => cambiar('telefono', e.target.value)}
                      className={`w-full rounded-lg border px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 ${
                        errores.telefono ? 'border-red-400' : 'border-slate-300'
                      }`}
                      aria-label="Número de teléfono"
                    />
                  </div>
                  {errores.telefono && <p className="mt-1 text-xs text-red-600">{errores.telefono}</p>}
                </div>
                <Selector
                  etiqueta="Tipo de teléfono"
                  obligatorio
                  valor={ficha.telefono_tipo}
                  onChange={(v) => cambiar('telefono_tipo', v)}
                  opciones={TIPOS_DE_TELEFONO}
                  error={errores.telefono_tipo}
                />
                <Selector
                  etiqueta="Género"
                  obligatorio
                  valor={ficha.genero}
                  onChange={(v) => cambiar('genero', v)}
                  opciones={GENEROS}
                  error={errores.genero}
                />
                <Sugerido
                  etiqueta="Nacionalidad"
                  obligatorio
                  valor={ficha.nacionalidad}
                  onChange={(v) => cambiar('nacionalidad', v)}
                  sugerencias={PAISES_SUGERIDOS}
                  error={errores.nacionalidad}
                />
                <Sugerido
                  etiqueta="País de residencia"
                  obligatorio
                  valor={ficha.pais_residencia}
                  onChange={(v) => cambiar('pais_residencia', v)}
                  sugerencias={PAISES_SUGERIDOS}
                  error={errores.pais_residencia}
                />
                <Sugerido
                  etiqueta="Provincia"
                  obligatorio
                  valor={ficha.provincia}
                  onChange={(v) => cambiar('provincia', v)}
                  sugerencias={PROVINCIAS_DE_ECUADOR}
                  error={errores.provincia}
                />
                <Texto
                  etiqueta="Localidad"
                  obligatorio
                  valor={ficha.localidad}
                  onChange={(v) => cambiar('localidad', v)}
                  error={errores.localidad}
                  ayuda="La ciudad donde vives."
                />
                <div>
                  <p className="mb-1 block text-sm font-medium text-slate-700">
                    Fecha de nacimiento<span className="ml-0.5 text-red-500">*</span>
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min={1}
                      max={31}
                      placeholder="Día"
                      value={ficha.nacimientoDia}
                      onChange={(e) => cambiar('nacimientoDia', e.target.value)}
                      className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      aria-label="Día de nacimiento"
                    />
                    <select
                      value={ficha.nacimientoMes}
                      onChange={(e) => cambiar('nacimientoMes', e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      aria-label="Mes de nacimiento"
                    >
                      <option value="">Mes</option>
                      {MESES.map((m, i) => (
                        <option key={m} value={i + 1}>
                          {m}
                        </option>
                      ))}
                    </select>
                    <select
                      value={ficha.nacimientoAnio}
                      onChange={(e) => cambiar('nacimientoAnio', e.target.value)}
                      className="w-28 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                      aria-label="Año de nacimiento"
                    >
                      <option value="">Año</option>
                      {ANIOS_DE_NACIMIENTO.map((a) => (
                        <option key={a} value={a}>
                          {a}
                        </option>
                      ))}
                    </select>
                  </div>
                  {errores.nacimiento && <p className="mt-1 text-xs text-red-600">{errores.nacimiento}</p>}
                </div>
              </div>

              {/* Este es el primer paso, así que no hay «Anterior»: solo Continuar, a la derecha. */}
              <div className="flex items-center justify-end border-t border-slate-100 pt-4">
                <button
                  onClick={() => validarPersonales() && setPaso('adicional')}
                  className="flex items-center gap-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
                >
                  Continuar <ArrowRight size={15} />
                </button>
              </div>
            </div>
          )}

          {paso === 'adicional' && (
            <div className="space-y-8">
              <Seccion titulo="Educación" descripcion="Añade cada título por separado.">
                {ficha.educacion.map((e, i) => (
                  <Tarjeta key={i} onEliminar={() => quitarFila('educacion', i)}>
                    <div className="grid gap-4 sm:grid-cols-3">
                      <Texto
                        etiqueta="Título"
                        valor={t(e.titulo)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { titulo: v || null })}
                      />
                      <Sugerido
                        etiqueta="País"
                        valor={t(e.pais)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { pais: v || null })}
                        sugerencias={PAISES_SUGERIDOS}
                      />
                      <Texto
                        etiqueta="Institución"
                        valor={t(e.institucion)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { institucion: v || null })}
                      />
                      <Sugerido
                        etiqueta="Área de estudio"
                        valor={t(e.area_estudio)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { area_estudio: v || null })}
                        sugerencias={AREAS_DE_ESTUDIO_SUGERIDAS}
                      />
                      <Selector
                        etiqueta="Nivel de estudio"
                        valor={t(e.nivel_estudio)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { nivel_estudio: v || null })}
                        opciones={NIVELES_DE_ESTUDIO}
                      />
                      <Selector
                        etiqueta="Estado de estudio"
                        valor={t(e.estado_estudio)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { estado_estudio: v || null })}
                        opciones={ESTADOS_DE_ESTUDIO}
                      />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-3">
                        <MesYAnio
                          etiqueta="Fecha de inicio"
                          mes={e.inicio_mes}
                          anio={e.inicio_anio}
                          onChange={(mes, anio) =>
                            cambiarFila<EducacionItem>('educacion', i, { inicio_mes: mes, inicio_anio: anio })
                          }
                        />
                        <Casilla
                          etiqueta="Actualmente asisto"
                          valor={e.actualmente}
                          onChange={(v) =>
                            cambiarFila<EducacionItem>('educacion', i, {
                              actualmente: v,
                              ...(v ? { fin_mes: null, fin_anio: null } : {}),
                            })
                          }
                        />
                        <MesYAnio
                          etiqueta="Finalización (o prevista)"
                          mes={e.fin_mes}
                          anio={e.fin_anio}
                          deshabilitado={e.actualmente}
                          onChange={(mes, anio) =>
                            cambiarFila<EducacionItem>('educacion', i, { fin_mes: mes, fin_anio: anio })
                          }
                        />
                      </div>
                      <Area
                        etiqueta="Descripción"
                        valor={t(e.descripcion)}
                        onChange={(v) => cambiarFila<EducacionItem>('educacion', i, { descripcion: v || null })}
                        filas={8}
                      />
                    </div>
                  </Tarjeta>
                ))}
                <BotonAnadir
                  texto="Añadir educación"
                  onClick={() => cambiar('educacion', [...ficha.educacion, { ...EDUCACION_VACIA }])}
                />
                <div>
                  <p className="mb-2 text-sm font-medium text-slate-700">
                    ¿Tienes los estudios secundarios completos?
                  </p>
                  <div className="flex gap-6">
                    {[
                      { texto: 'Sí', valor: true },
                      { texto: 'No', valor: false },
                    ].map((o) => (
                      <label key={o.texto} className="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="radio"
                          name="secundarios"
                          checked={ficha.estudios_secundarios_completos === o.valor}
                          onChange={() => cambiar('estudios_secundarios_completos', o.valor)}
                          className="h-4 w-4 border-slate-300 text-brand-600 focus:ring-brand-500"
                        />
                        {o.texto}
                      </label>
                    ))}
                  </div>
                </div>
              </Seccion>

              <Seccion titulo="Idiomas">
                {ficha.idiomas.map((idioma, i) => (
                  <Tarjeta key={i} onEliminar={() => quitarFila('idiomas', i)}>
                    <div className="grid gap-4 sm:grid-cols-3">
                      <Sugerido
                        etiqueta="Idioma"
                        valor={idioma.idioma}
                        onChange={(v) => cambiarFila<IdiomaItem>('idiomas', i, { idioma: v })}
                        sugerencias={IDIOMAS_SUGERIDOS}
                      />
                      <Selector
                        etiqueta="Nivel escrito"
                        valor={t(idioma.nivel_escrito)}
                        onChange={(v) => cambiarFila<IdiomaItem>('idiomas', i, { nivel_escrito: v || null })}
                        opciones={NIVELES_DE_IDIOMA}
                      />
                      <Selector
                        etiqueta="Nivel oral"
                        valor={t(idioma.nivel_oral)}
                        onChange={(v) => cambiarFila<IdiomaItem>('idiomas', i, { nivel_oral: v || null })}
                        opciones={NIVELES_DE_IDIOMA}
                      />
                    </div>
                  </Tarjeta>
                ))}
                <BotonAnadir
                  texto="Añadir idioma"
                  onClick={() => cambiar('idiomas', [...ficha.idiomas, { ...IDIOMA_VACIO }])}
                />
              </Seccion>

              <Seccion titulo="Experiencia laboral">
                {ficha.experiencia.map((x, i) => (
                  <Tarjeta key={i} onEliminar={() => quitarFila('experiencia', i)}>
                    <div className="grid gap-4 sm:grid-cols-3">
                      <Texto
                        etiqueta="Nombre del puesto"
                        valor={t(x.puesto)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { puesto: v || null })}
                      />
                      <Selector
                        etiqueta="Jerarquía"
                        valor={t(x.jerarquia)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { jerarquia: v || null })}
                        opciones={JERARQUIAS}
                      />
                      <Texto
                        etiqueta="Empresa / negocio"
                        valor={t(x.empresa)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { empresa: v || null })}
                      />
                      <Sugerido
                        etiqueta="País"
                        valor={t(x.pais)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { pais: v || null })}
                        sugerencias={PAISES_SUGERIDOS}
                      />
                      <Sugerido
                        etiqueta="Tipo de industria"
                        valor={t(x.industria)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { industria: v || null })}
                        sugerencias={INDUSTRIAS_SUGERIDAS}
                      />
                      <Sugerido
                        etiqueta="Área de trabajo"
                        valor={t(x.area_trabajo)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { area_trabajo: v || null })}
                        sugerencias={AREAS_DE_TRABAJO_SUGERIDAS}
                      />
                      <Texto
                        etiqueta="Subárea de trabajo"
                        valor={t(x.subarea_trabajo)}
                        onChange={(v) =>
                          cambiarFila<ExperienciaItem>('experiencia', i, { subarea_trabajo: v || null })
                        }
                      />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-3">
                        <MesYAnio
                          etiqueta="Fecha de inicio"
                          mes={x.inicio_mes}
                          anio={x.inicio_anio}
                          onChange={(mes, anio) =>
                            cambiarFila<ExperienciaItem>('experiencia', i, { inicio_mes: mes, inicio_anio: anio })
                          }
                        />
                        <Casilla
                          etiqueta="Actualmente trabajo aquí"
                          valor={x.actualmente}
                          onChange={(v) =>
                            cambiarFila<ExperienciaItem>('experiencia', i, {
                              actualmente: v,
                              ...(v ? { fin_mes: null, fin_anio: null } : {}),
                            })
                          }
                        />
                        <MesYAnio
                          etiqueta="Fecha de finalización"
                          mes={x.fin_mes}
                          anio={x.fin_anio}
                          deshabilitado={x.actualmente}
                          onChange={(mes, anio) =>
                            cambiarFila<ExperienciaItem>('experiencia', i, { fin_mes: mes, fin_anio: anio })
                          }
                        />
                      </div>
                      <Area
                        etiqueta="Descripción"
                        valor={t(x.descripcion)}
                        onChange={(v) => cambiarFila<ExperienciaItem>('experiencia', i, { descripcion: v || null })}
                        filas={8}
                      />
                    </div>
                  </Tarjeta>
                ))}
                <BotonAnadir
                  texto="Añadir experiencia"
                  onClick={() => cambiar('experiencia', [...ficha.experiencia, { ...EXPERIENCIA_VACIA }])}
                />
              </Seccion>

              <Seccion titulo="Redes">
                <Texto
                  etiqueta="LinkedIn"
                  tipo="url"
                  placeholder="www.linkedin.com/in/tu-perfil"
                  valor={ficha.linkedin_url}
                  onChange={(v) => cambiar('linkedin_url', v)}
                />
                {ficha.otras_redes.map((r, i) => (
                  <div key={i} className="grid gap-4 sm:grid-cols-[1fr_2fr_auto] sm:items-end">
                    <Texto
                      etiqueta="Red"
                      valor={r.red}
                      onChange={(v) => {
                        const lista = [...ficha.otras_redes]
                        lista[i] = { ...lista[i], red: v }
                        cambiar('otras_redes', lista)
                      }}
                    />
                    <Texto
                      etiqueta="Enlace"
                      tipo="url"
                      valor={r.url}
                      onChange={(v) => {
                        const lista = [...ficha.otras_redes]
                        lista[i] = { ...lista[i], url: v }
                        cambiar('otras_redes', lista)
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => quitarFila('otras_redes', i)}
                      className="mb-2 flex items-center gap-1 text-xs font-medium text-red-600 hover:underline"
                    >
                      <Trash2 size={13} /> Quitar
                    </button>
                  </div>
                ))}
                <BotonAnadir
                  texto="Añadir otra red social"
                  onClick={() => cambiar('otras_redes', [...ficha.otras_redes, { red: '', url: '' }])}
                />
              </Seccion>

              <Seccion titulo="Archivo adjunto" descripcion="Tamaño máximo: 15 MB. Formatos: PDF, DOCX, JPG o PNG.">
                <div className="flex flex-wrap items-center gap-3">
                  {ficha.cv_documento_url ? (
                    <span className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800">
                      <FileCheck2 size={16} /> {nombreDelCv ?? 'Currículum adjunto'}
                    </span>
                  ) : (
                    <span className="text-sm text-slate-500">Todavía no has adjuntado tu currículum.</span>
                  )}
                  <label className="cursor-pointer rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
                    <input
                      type="file"
                      accept=".pdf,.docx,.jpg,.jpeg,.png"
                      className="hidden"
                      onChange={adjuntarCv}
                    />
                    {ficha.cv_documento_url ? 'Cambiar archivo' : 'Adjuntar currículum'}
                  </label>
                </div>
              </Seccion>

              <Seccion titulo="Expectativas personales">
                <Area
                  etiqueta="Mensaje adicional"
                  valor={ficha.expectativas}
                  onChange={(v) => cambiar('expectativas', v)}
                />
              </Seccion>

              {vacante.preguntas_filtro.length > 0 && (
                <Seccion titulo="Preguntas de la vacante">
                  {vacante.preguntas_filtro.map((p) => (
                    <div key={p.id}>
                      <p className="mb-1 block text-sm font-medium text-slate-700">{p.pregunta}</p>
                      {p.opciones && p.opciones.length > 0 ? (
                        <select
                          value={respuestas[p.id] ?? ''}
                          onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        >
                          <option value="">Seleccione una opción</option>
                          {p.opciones.map((o) => (
                            <option key={o} value={o}>
                              {o}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          value={respuestas[p.id] ?? ''}
                          onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        />
                      )}
                    </div>
                  ))}
                </Seccion>
              )}

              <div className="border-t border-slate-100 pt-4">
                <Casilla
                  valor={ficha.acepta_privacidad}
                  onChange={(v) => cambiar('acepta_privacidad', v)}
                  etiqueta={
                    <>
                      He leído y acepto la política de privacidad
                      <span className="ml-0.5 text-red-500">*</span>
                    </>
                  }
                />
                {!ficha.acepta_privacidad && (
                  <p className="mt-1 text-xs text-slate-500">
                    Sin esto no podemos guardar tus datos ni tenerte en cuenta para la vacante.
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                <button
                  onClick={() => setPaso('personales')}
                  className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
                >
                  <ArrowLeft size={15} /> Anterior
                </button>
                <button
                  onClick={enviar}
                  disabled={enviando || !ficha.acepta_privacidad}
                  className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  {enviando && <Loader2 size={15} className="animate-spin" />}
                  Enviar postulación
                </button>
              </div>
            </div>
          )}

          {paso === 'listo' && (
            <div className="space-y-3 py-6 text-center">
              <CheckCircle2 className="mx-auto text-green-600" size={40} />
              <h2 className="text-base font-semibold text-slate-900">Postulación enviada</h2>
              <p className="text-sm text-slate-500">
                Recibimos tus datos para <strong>{vacante.titulo}</strong>. Si tu perfil encaja, te
                escribiremos a {ficha.email}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
