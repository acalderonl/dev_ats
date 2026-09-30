import { useEffect, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { UploadCloud, FileCheck2, Loader2, CheckCircle2, ArrowLeft, ArrowRight } from 'lucide-react'
import { toast } from 'sonner'
import { publicService } from '@/services/publicService'
import { ApiError } from '@/lib/apiClient'
import type { VacantePublica } from '@/types'

type Step = 'upload' | 'revisar' | 'preguntas' | 'confirmacion'

interface FormState {
  nombres: string
  apellidos: string
  cedula: string
  email: string
  telefono: string
  edad: string
  institucionSecundaria: string
  tituloSecundaria: string
  institucionSuperior: string
  tituloSuperior: string
  nivelInstruccion: string
  cargoAnterior: string
  empresaAnterior: string
}

const FORM_VACIO: FormState = {
  nombres: '',
  apellidos: '',
  cedula: '',
  email: '',
  telefono: '',
  edad: '',
  institucionSecundaria: '',
  tituloSecundaria: '',
  institucionSuperior: '',
  tituloSuperior: '',
  nivelInstruccion: '',
  cargoAnterior: '',
  empresaAnterior: '',
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

export function PostularView() {
  const { slug } = useParams<{ slug: string }>()
  const [vacante, setVacante] = useState<VacantePublica | null>(null)
  const [expirada, setExpirada] = useState(false)
  const [notFound, setNotFound] = useState(false)
  const [loadingVacante, setLoadingVacante] = useState(true)

  const [step, setStep] = useState<Step>('upload')
  const [parsing, setParsing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState<FormState>(FORM_VACIO)
  const [respuestas, setRespuestas] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!slug) return
    publicService
      .getVacante(slug)
      .then(setVacante)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 410) setExpirada(true)
        else if (err instanceof ApiError && err.status === 404) setNotFound(true)
        else toast.error(errorMessage(err))
      })
      .finally(() => setLoadingVacante(false))
  }, [slug])

  if (expirada) return <Navigate to="/vacante-expirada" replace />

  if (loadingVacante) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="animate-spin text-slate-400" size={28} />
      </div>
    )
  }

  if (notFound || !vacante) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 text-center">
        <p className="text-sm text-slate-500">Vacante no encontrada.</p>
      </div>
    )
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setParsing(true)
    try {
      const parsed = await publicService.parseCv(file)
      setForm((f) => ({
        ...f,
        nombres: parsed.nombres ?? f.nombres,
        apellidos: parsed.apellidos ?? f.apellidos,
        cedula: parsed.cedula ?? f.cedula,
        email: parsed.email ?? f.email,
        telefono: parsed.telefono ?? f.telefono,
        edad: parsed.edad ? String(parsed.edad) : f.edad,
        institucionSuperior: parsed.formacion_superior?.institucion ?? f.institucionSuperior,
        tituloSuperior: parsed.formacion_superior?.titulo ?? f.tituloSuperior,
        nivelInstruccion: parsed.nivel_instruccion ?? f.nivelInstruccion,
        cargoAnterior: parsed.experiencia_laboral[0]?.cargo ?? f.cargoAnterior,
        empresaAnterior: parsed.experiencia_laboral[0]?.empresa ?? f.empresaAnterior,
      }))
      toast.success('CV analizado. Revisa y completa los datos faltantes.')
      setStep('revisar')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setParsing(false)
    }
  }

  async function handleSubmitFinal() {
    if (!slug) return
    setSubmitting(true)
    try {
      await publicService.postular(slug, {
        nombres: form.nombres,
        apellidos: form.apellidos,
        cedula: form.cedula,
        email: form.email,
        telefono: form.telefono || undefined,
        edad: form.edad ? Number(form.edad) : undefined,
        formacion_secundaria: { institucion: form.institucionSecundaria, titulo: form.tituloSecundaria },
        formacion_superior: { institucion: form.institucionSuperior, titulo: form.tituloSuperior, estado: 'graduado' },
        nivel_instruccion: form.nivelInstruccion || undefined,
        titulos: form.tituloSuperior ? [form.tituloSuperior] : [],
        experiencia_laboral: form.cargoAnterior
          ? [{ cargo: form.cargoAnterior, empresa: form.empresaAnterior, fecha_desde: '2021-01-01', fecha_hasta: null, actualmente: true }]
          : [],
        respuestas_filtro: respuestas,
        origen: 'Directo',
      })
      setStep('confirmacion')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 sm:py-12">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            ATS
          </div>
          <h1 className="text-lg font-semibold text-slate-900">{vacante.titulo}</h1>
          <p className="text-sm text-slate-500">
            {vacante.cargo_nombre} · Vence el {new Date(vacante.fecha_limite).toLocaleDateString('es-EC')}
          </p>
        </div>

        {step !== 'confirmacion' && (
          <div className="mb-6 flex items-center justify-center gap-2 text-xs font-medium text-slate-400">
            {['upload', 'revisar', 'preguntas'].map((s, i) => (
              <div key={s} className={`flex items-center gap-2 ${step === s ? 'text-brand-600' : ''}`}>
                <span className={`flex h-6 w-6 items-center justify-center rounded-full border ${step === s ? 'border-brand-600 bg-brand-50' : 'border-slate-300'}`}>
                  {i + 1}
                </span>
                {i < 2 && <span className="h-px w-6 bg-slate-300" />}
              </div>
            ))}
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          {step === 'upload' && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-800">Paso 1: Sube tu hoja de vida</h2>
              <p className="text-sm text-slate-500">{vacante.descripcion}</p>
              <label
                className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
                  parsing ? 'border-brand-300 bg-brand-50' : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50'
                }`}
              >
                <input type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} disabled={parsing} />
                {parsing ? (
                  <>
                    <Loader2 className="animate-spin text-brand-600" size={28} />
                    <p className="mt-3 text-sm font-medium text-brand-700">Analizando CV...</p>
                  </>
                ) : (
                  <>
                    <UploadCloud className="text-slate-400" size={28} />
                    <p className="mt-3 text-sm font-medium text-slate-600">Arrastra tu CV o haz clic para subirlo</p>
                    <p className="mt-1 text-xs text-slate-400">Formatos permitidos: PDF, DOCX</p>
                  </>
                )}
              </label>
              <button onClick={() => setStep('revisar')} className="w-full text-center text-xs text-slate-400 underline hover:text-slate-600">
                Prefiero llenar el formulario manualmente
              </button>
            </div>
          )}

          {step === 'revisar' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                <FileCheck2 size={16} className="text-emerald-500" /> Paso 2: Revisa y confirma tus datos
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Field label="Nombres" value={form.nombres} onChange={(v) => setForm({ ...form, nombres: v })} />
                <Field label="Apellidos" value={form.apellidos} onChange={(v) => setForm({ ...form, apellidos: v })} />
                <Field label="Cédula" value={form.cedula} onChange={(v) => setForm({ ...form, cedula: v })} />
                <Field label="Edad" type="number" value={form.edad} onChange={(v) => setForm({ ...form, edad: v })} />
                <Field label="Correo" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
                <Field label="Teléfono" value={form.telefono} onChange={(v) => setForm({ ...form, telefono: v })} />
                <Field label="Formación superior" value={form.tituloSuperior} onChange={(v) => setForm({ ...form, tituloSuperior: v })} />
                <Field label="Nivel de instrucción" value={form.nivelInstruccion} onChange={(v) => setForm({ ...form, nivelInstruccion: v })} />
                <Field label="Último cargo" value={form.cargoAnterior} onChange={(v) => setForm({ ...form, cargoAnterior: v })} />
                <Field label="Última empresa" value={form.empresaAnterior} onChange={(v) => setForm({ ...form, empresaAnterior: v })} />
              </div>
              <div className="flex justify-between pt-2">
                <button onClick={() => setStep('upload')} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
                  <ArrowLeft size={15} /> Atrás
                </button>
                <button
                  onClick={() => setStep('preguntas')}
                  disabled={!form.nombres || !form.apellidos || !form.cedula || !form.email}
                  className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  Continuar <ArrowRight size={15} />
                </button>
              </div>
            </div>
          )}

          {step === 'preguntas' && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-800">Paso 3: Preguntas del empleador</h2>
              {vacante.preguntas_filtro.length === 0 && (
                <p className="text-sm text-slate-400">Este cargo no tiene preguntas filtro configuradas.</p>
              )}
              {vacante.preguntas_filtro.map((p) => (
                <div key={p.id}>
                  <label className="mb-1 block text-sm font-medium text-slate-700">{p.pregunta}</label>
                  {p.tipo_respuesta === 'booleano' ? (
                    <select
                      required
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      value={respuestas[p.pregunta] ?? ''}
                      onChange={(e) => setRespuestas({ ...respuestas, [p.pregunta]: e.target.value })}
                    >
                      <option value="">Selecciona...</option>
                      <option value="Sí">Sí</option>
                      <option value="No">No</option>
                    </select>
                  ) : p.tipo_respuesta === 'unica' && p.opciones ? (
                    <select
                      required
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      value={respuestas[p.pregunta] ?? ''}
                      onChange={(e) => setRespuestas({ ...respuestas, [p.pregunta]: e.target.value })}
                    >
                      <option value="">Selecciona...</option>
                      {p.opciones.map((op) => (
                        <option key={op} value={op}>
                          {op}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      required
                      type={p.tipo_respuesta === 'numero' ? 'number' : 'text'}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      value={respuestas[p.pregunta] ?? ''}
                      onChange={(e) => setRespuestas({ ...respuestas, [p.pregunta]: e.target.value })}
                    />
                  )}
                </div>
              ))}
              <div className="flex justify-between pt-2">
                <button onClick={() => setStep('revisar')} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
                  <ArrowLeft size={15} /> Atrás
                </button>
                <button
                  onClick={handleSubmitFinal}
                  disabled={submitting}
                  className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
                >
                  {submitting && <Loader2 size={15} className="animate-spin" />} Enviar Postulación
                </button>
              </div>
            </div>
          )}

          {step === 'confirmacion' && (
            <div className="flex flex-col items-center py-6 text-center">
              <CheckCircle2 className="text-emerald-500" size={40} />
              <h2 className="mt-3 text-base font-semibold text-slate-900">¡Postulación enviada con éxito!</h2>
              <p className="mt-1 max-w-sm text-sm text-slate-500">
                Hemos recibido tu postulación a <strong>{vacante.titulo}</strong>. Nuestro equipo la revisará pronto.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-slate-500">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
    </div>
  )
}
