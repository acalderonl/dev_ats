import { useEffect, useState } from 'react'
import { AlertTriangle, Check, Clock, Linkedin, Loader2, Plug, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { configuracionService } from '@/services/vacantesService'
import { ApiError } from '@/lib/apiClient'
import type {
  CifradoSmtp,
  ConfiguracionGeneral,
  EstadoLinkedIn,
  Jornada,
  TipoDeCorreo,
} from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

/** La página de vuelta del OAuth de LinkedIn en este sitio. Es la que hay que
 *  registrar en la aplicación de LinkedIn, y tiene que coincidir exactamente. */
const RETORNO_DE_ESTE_SITIO = `${window.location.origin}/configuracion/linkedin`

/** Campo de texto normal. */
function Campo({
  etiqueta,
  valor,
  onChange,
  ayuda,
  placeholder,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  ayuda?: string
  placeholder?: string
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{etiqueta}</label>
      <input
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      {ayuda && <p className="mt-1 text-xs text-slate-500">{ayuda}</p>}
    </div>
  )
}

/**
 * Campo de secreto.
 *
 * Nunca muestra el valor guardado, porque la API no lo devuelve: muestra si está
 * puesto y los últimos cuatro caracteres. Dejarlo vacío **no lo borra**; para eso
 * está el botón, que es explícito.
 */
function CampoSecreto({
  etiqueta,
  valor,
  onChange,
  configurado,
  pista,
  ayuda,
}: {
  etiqueta: string
  valor: string
  onChange: (v: string) => void
  configurado: boolean
  pista: string | null
  ayuda?: string
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">{etiqueta}</label>
        {configurado && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <Check size={12} /> Configurado {pista}
          </span>
        )}
      </div>
      <input
        type="password"
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        placeholder={configurado ? 'Déjalo vacío para no cambiarlo' : 'Sin configurar'}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
      />
      {ayuda && <p className="mt-1 text-xs text-slate-500">{ayuda}</p>}
      {configurado && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="mt-1 text-xs text-red-600 hover:underline"
          title="Lo borra al guardar"
        >
          Borrar el valor guardado
        </button>
      )}
    </div>
  )
}

export function ConfiguracionView() {
  const [config, setConfig] = useState<ConfiguracionGeneral | null>(null)
  const [estadoLinkedIn, setEstadoLinkedIn] = useState<EstadoLinkedIn | null>(null)
  const [jornadas, setJornadas] = useState<Jornada[]>([])
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)

  // Lo que el usuario escribe. Separado de `config` porque los secretos no se
  // devuelven: aquí vacío significa "no lo toques", no "bórralo".
  const [edicion, setEdicion] = useState<Record<string, string>>({})
  const [jornadaNueva, setJornadaNueva] = useState({ nombre: '', horas: '' })
  const [probando, setProbando] = useState(false)
  const [resultadoPrueba, setResultadoPrueba] = useState<{ ok: boolean; mensaje: string } | null>(null)

  // Sin elegir, Gmail: es lo que había antes de existir el selector, y no debe
  // cambiarle la conexión a quien ya la tenía puesta.
  const tipoDeCorreo = (edicion.correo_tipo || 'gmail') as TipoDeCorreo
  const cifrado = (edicion.smtp_cifrado || 'starttls') as CifradoSmtp
  const correoListo =
    tipoDeCorreo === 'gmail'
      ? config?.gmail_password_app_configurado && Boolean(config?.gmail_remitente)
      : config?.smtp_password_configurado && Boolean(config?.smtp_servidor && config?.smtp_remitente)

  async function recargar() {
    const [c, e, j] = await Promise.all([
      configuracionService.leer(),
      configuracionService.estadoLinkedIn(),
      configuracionService.jornadas(),
    ])
    setConfig(c)
    setEstadoLinkedIn(e)
    setJornadas(j)
    setEdicion({
      empresa_nombre: c.empresa_nombre ?? '',
      linkedin_client_id: c.linkedin_client_id ?? '',
      linkedin_redirect_uri: c.linkedin_redirect_uri ?? '',
      correo_tipo: c.correo_tipo ?? 'gmail',
      gmail_remitente: c.gmail_remitente ?? '',
      smtp_servidor: c.smtp_servidor ?? '',
      smtp_puerto: c.smtp_puerto ?? '',
      smtp_cifrado: c.smtp_cifrado ?? 'starttls',
      smtp_usuario: c.smtp_usuario ?? '',
      smtp_remitente: c.smtp_remitente ?? '',
      dominios_corporativos: c.dominios_corporativos ?? '',
      linkedin_client_secret: '',
      gmail_password_app: '',
      smtp_password: '',
    })
  }

  useEffect(() => {
    recargar()
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setCargando(false))
  }, [])

  function actualizar(clave: string, valor: string) {
    setEdicion((e) => ({ ...e, [clave]: valor }))
  }

  async function guardar() {
    setGuardando(true)
    try {
      // Los secretos vacíos no se mandan: mandarlos los borraría.
      const payload = { ...edicion }
      for (const clave of ['linkedin_client_secret', 'gmail_password_app', 'smtp_password']) {
        if (!payload[clave]) delete payload[clave]
      }
      await configuracionService.guardar(payload)
      await recargar()
      setResultadoPrueba(null)
      toast.success('Configuración guardada')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function probarCorreo() {
    setProbando(true)
    setResultadoPrueba(null)
    try {
      setResultadoPrueba(await configuracionService.probarCorreo())
    } catch (err) {
      setResultadoPrueba({ ok: false, mensaje: errorMessage(err) })
    } finally {
      setProbando(false)
    }
  }

  async function conectarLinkedIn() {
    try {
      const { url } = await configuracionService.conectarLinkedIn()
      window.location.href = url
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function desconectarLinkedIn() {
    try {
      await configuracionService.desconectarLinkedIn()
      await recargar()
      toast.success('Cuenta de LinkedIn desconectada')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function crearJornada() {
    if (!jornadaNueva.nombre.trim() || !jornadaNueva.horas) return
    try {
      await configuracionService.crearJornada(jornadaNueva)
      setJornadas(await configuracionService.jornadas())
      setJornadaNueva({ nombre: '', horas: '' })
      toast.success('Jornada creada')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  async function eliminarJornada(id: number) {
    try {
      await configuracionService.eliminarJornada(id)
      setJornadas(await configuracionService.jornadas())
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  if (cargando || !config) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  const caducaPronto =
    estadoLinkedIn?.expira_en &&
    new Date(estadoLinkedIn.expira_en).getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Configuración</h1>
        <p className="text-sm text-slate-500">
          Credenciales y parámetros de la empresa. Los secretos se guardan cifrados y no vuelven a
          mostrarse.
        </p>
      </div>

      <Card className="p-5 sm:p-6">
        <h2 className="mb-4 text-sm font-semibold text-slate-800">Empresa</h2>
        <div className="space-y-4">
          <Campo
            etiqueta="Nombre de la empresa"
            valor={edicion.empresa_nombre ?? ''}
            onChange={(v) => actualizar('empresa_nombre', v)}
            placeholder="ACME S.A."
          />
          <Campo
            etiqueta="Dominios corporativos"
            valor={edicion.dominios_corporativos ?? ''}
            onChange={(v) => actualizar('dominios_corporativos', v)}
            placeholder="empresa.com, empresa.ec"
            ayuda="Separados por comas. Una vacante interna solo se envía a correos de estos dominios. Si lo dejas vacío, no se restringe."
          />
        </div>
      </Card>

      <Card className="p-5 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800">LinkedIn</h2>
          {estadoLinkedIn?.cuenta_conectada ? (
            <Badge tone="green">Conectado</Badge>
          ) : (
            <Badge tone="slate">Sin conectar</Badge>
          )}
        </div>

        <div className="mb-4 space-y-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          <p>
            <strong className="text-slate-800">Esto es opcional.</strong> Para llevar una vacante a
            LinkedIn no hace falta conectar nada aquí: el botón <strong>LinkedIn</strong> de la
            tarjeta de la vacante copia el texto y abre el compositor para que la publiques tú.
          </p>
          <p>
            Conectar sirve para lo otro: que el sistema <strong>publique solo</strong>, sin abrir
            LinkedIn. Para eso LinkedIn exige una aplicación propia —no hay otra vía—, y los tres
            datos de abajo salen de ella.
          </p>
          <p className="flex items-start gap-1.5 text-amber-800">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            <span>
              Por cualquiera de las dos vías sale en <strong>el muro de quien conecta su cuenta</strong>.
              La página de empresa y el tablón de empleos exigen ser partner aprobado por LinkedIn.
            </span>
          </p>
        </div>

        <div className="space-y-4">
          <Campo
            etiqueta="Client ID"
            valor={edicion.linkedin_client_id ?? ''}
            onChange={(v) => actualizar('linkedin_client_id', v)}
            ayuda="De tu app en developer.linkedin.com, pestaña Auth."
          />
          <CampoSecreto
            etiqueta="Client Secret"
            valor={edicion.linkedin_client_secret ?? ''}
            onChange={(v) => actualizar('linkedin_client_secret', v)}
            configurado={config.linkedin_client_secret_configurado}
            pista={config.linkedin_client_secret_pista}
          />
          <div>
            <Campo
              etiqueta="Redirect URI"
              valor={edicion.linkedin_redirect_uri ?? ''}
              onChange={(v) => actualizar('linkedin_redirect_uri', v)}
              placeholder={RETORNO_DE_ESTE_SITIO}
              ayuda="Tiene que coincidir carácter por carácter con la que registraste en LinkedIn; si no, la conexión se corta ahí."
            />
            {edicion.linkedin_redirect_uri !== RETORNO_DE_ESTE_SITIO && (
              <button
                type="button"
                onClick={() => actualizar('linkedin_redirect_uri', RETORNO_DE_ESTE_SITIO)}
                className="mt-1 text-xs text-brand-600 hover:underline"
              >
                Usar la de este sitio: {RETORNO_DE_ESTE_SITIO}
              </button>
            )}
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4">
          {estadoLinkedIn?.cuenta_conectada ? (
            <>
              <div className="flex-1 text-xs text-slate-600">
                Conectado como <strong>{estadoLinkedIn.nombre_en_linkedin}</strong>
                {estadoLinkedIn.expira_en && (
                  <span className={caducaPronto ? 'text-amber-600' : 'text-slate-400'}>
                    {' '}
                    · caduca el {new Date(estadoLinkedIn.expira_en).toLocaleDateString()}
                  </span>
                )}
              </div>
              <button
                onClick={desconectarLinkedIn}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                Desconectar
              </button>
            </>
          ) : (
            <>
              <p className="flex-1 text-xs text-slate-500">
                {estadoLinkedIn?.credenciales_configuradas
                  ? 'Credenciales listas. Conecta tu cuenta para poder publicar.'
                  : 'Guarda Client ID, Secret y Redirect URI antes de conectar.'}
              </p>
              <button
                onClick={conectarLinkedIn}
                disabled={!estadoLinkedIn?.credenciales_configuradas}
                className="flex items-center gap-1.5 rounded-lg bg-[#0a66c2] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#004182] disabled:opacity-50"
              >
                <Linkedin size={14} /> Conectar cuenta
              </button>
            </>
          )}
        </div>

        {estadoLinkedIn?.cuenta_conectada && caducaPronto && (
          <p className="mt-2 flex items-start gap-1.5 text-xs text-amber-700">
            <Clock size={13} className="mt-0.5 shrink-0" />
            El acceso caduca pronto. LinkedIn no da renovación automática fuera del programa de
            partners: habrá que volver a conectar.
          </p>
        )}
      </Card>

      <Card className="p-5 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800">Correo</h2>
          {correoListo ? <Badge tone="green">Configurado</Badge> : <Badge tone="slate">Sin configurar</Badge>}
        </div>

        {/* Se eligen los dos por separado porque lo que hay que pedirle a una persona
            es distinto: para Gmail, una contraseña de aplicación; para un servidor
            propio, cinco datos que le tiene que dar su departamento de sistemas. */}
        <div className="mb-5 grid grid-cols-2 gap-3">
          {(
            [
              ['gmail', 'Gmail / Workspace', 'Servidor y puerto ya puestos'],
              ['smtp', 'Servidor propio', 'Correo institucional, cualquier SMTP'],
            ] as [TipoDeCorreo, string, string][]
          ).map(([valor, titulo, detalle]) => (
            <button
              key={valor}
              type="button"
              onClick={() => actualizar('correo_tipo', valor)}
              className={`rounded-lg border p-3 text-left transition-colors ${
                tipoDeCorreo === valor
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <span
                className={`block text-sm font-medium ${
                  tipoDeCorreo === valor ? 'text-brand-700' : 'text-slate-700'
                }`}
              >
                {titulo}
              </span>
              <span className="mt-0.5 block text-xs text-slate-500">{detalle}</span>
            </button>
          ))}
        </div>

        {tipoDeCorreo === 'gmail' ? (
          <div className="space-y-4">
            <Campo
              etiqueta="Correo remitente"
              valor={edicion.gmail_remitente ?? ''}
              onChange={(v) => actualizar('gmail_remitente', v)}
              placeholder="talento@empresa.com"
            />
            <CampoSecreto
              etiqueta="Contraseña de aplicación"
              valor={edicion.gmail_password_app ?? ''}
              onChange={(v) => actualizar('gmail_password_app', v)}
              configurado={config.gmail_password_app_configurado}
              pista={config.gmail_password_app_pista}
              ayuda="No es la contraseña de la cuenta. Con la verificación en dos pasos activada, genérala en la cuenta de Google (16 caracteres)."
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <Campo
                  etiqueta="Servidor"
                  valor={edicion.smtp_servidor ?? ''}
                  onChange={(v) => actualizar('smtp_servidor', v)}
                  placeholder="mail.institucion.edu.ec"
                />
              </div>
              <Campo
                etiqueta="Puerto"
                valor={edicion.smtp_puerto ?? ''}
                onChange={(v) => actualizar('smtp_puerto', v)}
                placeholder="587"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Cifrado</label>
              <div className="grid grid-cols-3 gap-2">
                {(
                  [
                    ['starttls', 'STARTTLS', '587'],
                    ['ssl', 'SSL/TLS', '465'],
                    ['ninguna', 'Ninguno', '25'],
                  ] as [CifradoSmtp, string, string][]
                ).map(([valor, titulo, puerto]) => (
                  <button
                    key={valor}
                    type="button"
                    onClick={() => {
                      actualizar('smtp_cifrado', valor)
                      // El puerto casi siempre va con el cifrado. Se propone, no se impone:
                      // solo se rellena si está vacío, para no pisar un puerto a medida.
                      if (!edicion.smtp_puerto) actualizar('smtp_puerto', puerto)
                    }}
                    className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                      cifrado === valor
                        ? 'border-brand-500 bg-brand-50 text-brand-700'
                        : 'border-slate-300 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {titulo}
                  </button>
                ))}
              </div>
              {cifrado === 'ninguna' && (
                <p className="mt-1 flex items-start gap-1.5 text-xs text-amber-700">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  Sin cifrado la contraseña viaja en claro por la red. Úsalo solo en un servidor
                  interno y de confianza.
                </p>
              )}
            </div>

            <Campo
              etiqueta="Correo remitente"
              valor={edicion.smtp_remitente ?? ''}
              onChange={(v) => actualizar('smtp_remitente', v)}
              placeholder="talento@institucion.edu.ec"
              ayuda="La dirección desde la que llegará el correo."
            />
            <Campo
              etiqueta="Usuario (opcional)"
              valor={edicion.smtp_usuario ?? ''}
              onChange={(v) => actualizar('smtp_usuario', v)}
              placeholder="Déjalo vacío si es el mismo que el remitente"
              ayuda="Algunos servidores piden entrar con otra cuenta, por ejemplo dominio\\usuario."
            />
            <CampoSecreto
              etiqueta="Contraseña"
              valor={edicion.smtp_password ?? ''}
              onChange={(v) => actualizar('smtp_password', v)}
              configurado={config.smtp_password_configurado}
              pista={config.smtp_password_pista}
            />
          </div>
        )}

        <div className="mt-5 flex items-center gap-3 border-t border-slate-100 pt-4">
          <p className="flex-1 text-xs text-slate-500">
            Se conecta y autentica sin enviar nada. Guarda antes de probar.
          </p>
          <button
            type="button"
            onClick={probarCorreo}
            disabled={probando}
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            {probando ? <Loader2 size={13} className="animate-spin" /> : <Plug size={13} />}
            Probar conexión
          </button>
        </div>

        {resultadoPrueba && (
          <p
            className={`mt-3 flex items-start gap-1.5 rounded-lg p-3 text-xs ${
              resultadoPrueba.ok ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-800'
            }`}
          >
            {resultadoPrueba.ok ? (
              <Check size={14} className="mt-0.5 shrink-0" />
            ) : (
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            )}
            {resultadoPrueba.mensaje}
          </p>
        )}
      </Card>

      <Card className="p-5 sm:p-6">
        <h2 className="mb-1 text-sm font-semibold text-slate-800">Jornadas laborales</h2>
        <p className="mb-4 text-xs text-slate-500">
          Alimentan el selector de horario de la vacante. La hora de salida se calcula con estas horas.
        </p>

        <div className="space-y-2">
          {jornadas.map((j) => (
            <div
              key={j.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2"
            >
              <span className="text-sm text-slate-700">{j.nombre}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500">{Number(j.horas)} h</span>
                <button
                  onClick={() => eliminarJornada(j.id)}
                  className="rounded-md p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                  title="Eliminar"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <input
              value={jornadaNueva.nombre}
              onChange={(e) => setJornadaNueva((j) => ({ ...j, nombre: e.target.value }))}
              placeholder="Nombre (ej. Jornada de 6 horas)"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <input
              type="number"
              step="0.5"
              min="0.5"
              max="24"
              value={jornadaNueva.horas}
              onChange={(e) => setJornadaNueva((j) => ({ ...j, horas: e.target.value }))}
              placeholder="Horas"
              className="w-24 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button
              onClick={crearJornada}
              className="flex items-center gap-1 rounded-lg border border-slate-300 px-3 text-sm text-slate-600 hover:bg-slate-50"
            >
              <Plus size={15} />
            </button>
          </div>
        </div>
      </Card>

      <button
        onClick={guardar}
        disabled={guardando}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {guardando && <Loader2 size={15} className="animate-spin" />}
        Guardar configuración
      </button>
    </div>
  )
}
