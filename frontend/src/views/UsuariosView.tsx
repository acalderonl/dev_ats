import { useEffect, useMemo, useState } from 'react'
import {
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  ShieldCheck,
  Trash2,
  UserCheck,
  UserCog,
  UserMinus,
} from 'lucide-react'
import { toast } from 'sonner'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { SelectorDePermisos } from '@/components/usuarios/SelectorDePermisos'
import { useAuthStore } from '@/store/authStore'
import { rolesService, usuariosService } from '@/services/usuariosService'
import { ApiError } from '@/lib/apiClient'
import type { Permiso, PermisosDeUsuario, Rol, Usuario } from '@/types'

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'Ocurrió un error inesperado'
}

const TONO_POR_ROL: Record<string, 'purple' | 'blue' | 'amber' | 'slate'> = {
  super_admin: 'purple',
  reclutador: 'blue',
  entrevistador: 'amber',
}

/** `jefe_de_area` se lee mejor como "Jefe de area". */
function comoSeLee(nombre: string): string {
  const texto = nombre.replace(/_/g, ' ')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

const FORM_USUARIO_VACIO = {
  email: '',
  nombres: '',
  apellidos: '',
  password: '',
  rol: '',
  activo: true,
}

export function UsuariosView() {
  const yo = useAuthStore((s) => s.user)

  const [pestana, setPestana] = useState<'usuarios' | 'inactivos' | 'roles'>('usuarios')
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [roles, setRoles] = useState<Rol[]>([])
  const [catalogo, setCatalogo] = useState<Permiso[]>([])
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)

  // Usuario
  const [modalUsuario, setModalUsuario] = useState(false)
  const [usuarioEnEdicion, setUsuarioEnEdicion] = useState<Usuario | null>(null)
  const [formUsuario, setFormUsuario] = useState(FORM_USUARIO_VACIO)
  const [usuarioAConfirmar, setUsuarioAConfirmar] = useState<Usuario | null>(null)
  const [claveDe, setClaveDe] = useState<Usuario | null>(null)
  const [claveNueva, setClaveNueva] = useState('')

  // Permisos de un usuario
  const [permisosDe, setPermisosDe] = useState<Usuario | null>(null)
  const [detallePermisos, setDetallePermisos] = useState<PermisosDeUsuario | null>(null)
  const [permisosElegidos, setPermisosElegidos] = useState<Set<string>>(new Set())

  // Rol
  const [modalRol, setModalRol] = useState(false)
  const [rolEnEdicion, setRolEnEdicion] = useState<Rol | null>(null)
  const [formRol, setFormRol] = useState({ nombre: '', descripcion: '' })
  const [permisosDelRol, setPermisosDelRol] = useState<Set<string>>(new Set())
  const [rolAEliminar, setRolAEliminar] = useState<Rol | null>(null)

  const rolesActivos = useMemo(() => roles.filter((r) => r.activo), [roles])
  const activos = useMemo(() => usuarios.filter((u) => u.activo), [usuarios])
  const inactivos = useMemo(() => usuarios.filter((u) => !u.activo), [usuarios])

  async function recargar() {
    const [u, r, c] = await Promise.all([
      usuariosService.list(),
      rolesService.list(),
      rolesService.catalogoDePermisos(),
    ])
    setUsuarios(u)
    setRoles(r)
    setCatalogo(c)
  }

  useEffect(() => {
    recargar()
      .catch((err) => toast.error(errorMessage(err)))
      .finally(() => setCargando(false))
  }, [])

  // ------------------------------------------------------------- Usuarios

  function abrirNuevoUsuario() {
    setUsuarioEnEdicion(null)
    setFormUsuario({ ...FORM_USUARIO_VACIO, rol: rolesActivos[0]?.nombre ?? '' })
    setModalUsuario(true)
  }

  function abrirEdicionUsuario(usuario: Usuario) {
    setUsuarioEnEdicion(usuario)
    setFormUsuario({
      email: usuario.email,
      nombres: usuario.nombres,
      apellidos: usuario.apellidos,
      password: '',
      rol: usuario.rol,
      activo: usuario.activo,
    })
    setModalUsuario(true)
  }

  async function guardarUsuario(e: React.FormEvent) {
    e.preventDefault()
    setGuardando(true)
    try {
      if (usuarioEnEdicion) {
        await usuariosService.update(usuarioEnEdicion.id, {
          email: formUsuario.email,
          nombres: formUsuario.nombres,
          apellidos: formUsuario.apellidos,
          rol: formUsuario.rol,
        })
        toast.success('Usuario actualizado')
      } else {
        await usuariosService.create(formUsuario)
        toast.success('Usuario creado')
      }
      await recargar()
      setModalUsuario(false)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function confirmarCambioDeEstado() {
    if (!usuarioAConfirmar) return
    setGuardando(true)
    try {
      await usuariosService.setActivo(usuarioAConfirmar.id, !usuarioAConfirmar.activo)
      await recargar()
      setUsuarioAConfirmar(null)
      toast.success(usuarioAConfirmar.activo ? 'Usuario desactivado' : 'Usuario activado')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function guardarClave(e: React.FormEvent) {
    e.preventDefault()
    if (!claveDe) return
    setGuardando(true)
    try {
      await usuariosService.restablecerClave(claveDe.id, claveNueva)
      toast.success(`Contraseña cambiada. Pásasela a ${claveDe.nombres} por un canal seguro.`)
      setClaveDe(null)
      setClaveNueva('')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  // ------------------------------------------------- Permisos de un usuario

  async function abrirPermisos(usuario: Usuario) {
    setPermisosDe(usuario)
    setDetallePermisos(null)
    try {
      const detalle = await usuariosService.permisosDe(usuario.id)
      setDetallePermisos(detalle)
      setPermisosElegidos(new Set(detalle.efectivos))
    } catch (err) {
      toast.error(errorMessage(err))
      setPermisosDe(null)
    }
  }

  async function guardarPermisos() {
    if (!permisosDe || !detallePermisos) return
    setGuardando(true)
    try {
      // Solo se mandan las DIFERENCIAS respecto al rol. Así, si mañana cambia la
      // plantilla del rol, este usuario la hereda en vez de quedarse con una copia.
      const delRol = new Set(detallePermisos.del_rol)
      const ajustes = catalogo
        .filter((p) => permisosElegidos.has(p.clave) !== delRol.has(p.clave))
        .map((p) => ({ clave: p.clave, concedido: permisosElegidos.has(p.clave) }))

      await usuariosService.ajustarPermisos(permisosDe.id, ajustes)
      toast.success(
        ajustes.length === 0
          ? 'Sin excepciones: este usuario usa los permisos de su rol'
          : `Guardado con ${ajustes.length} excepción(es) sobre su rol`,
      )
      setPermisosDe(null)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  // ------------------------------------------------------------------ Roles

  function abrirNuevoRol() {
    setRolEnEdicion(null)
    setFormRol({ nombre: '', descripcion: '' })
    setPermisosDelRol(new Set())
    setModalRol(true)
  }

  function abrirEdicionRol(rol: Rol) {
    setRolEnEdicion(rol)
    setFormRol({ nombre: rol.nombre, descripcion: rol.descripcion ?? '' })
    setPermisosDelRol(new Set(rol.permisos))
    setModalRol(true)
  }

  async function guardarRol(e: React.FormEvent) {
    e.preventDefault()
    setGuardando(true)
    try {
      if (rolEnEdicion) {
        await rolesService.update(rolEnEdicion.id, {
          // El nombre de un rol de sistema no se manda: el backend lo rechazaría.
          ...(rolEnEdicion.es_sistema ? {} : { nombre: formRol.nombre }),
          descripcion: formRol.descripcion || null,
          ...(rolEnEdicion.nombre === 'super_admin' ? {} : { permisos: [...permisosDelRol] }),
        })
        toast.success('Rol actualizado')
      } else {
        await rolesService.create({
          nombre: formRol.nombre,
          descripcion: formRol.descripcion || null,
          permisos: [...permisosDelRol],
        })
        toast.success('Rol creado')
      }
      await recargar()
      setModalRol(false)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  async function confirmarEliminarRol() {
    if (!rolAEliminar) return
    setGuardando(true)
    try {
      await rolesService.remove(rolAEliminar.id)
      await recargar()
      setRolAEliminar(null)
      toast.success('Rol eliminado')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setGuardando(false)
    }
  }

  function alternar(conjunto: Set<string>, setter: (s: Set<string>) => void) {
    return (clave: string, marcado: boolean) => {
      const copia = new Set(conjunto)
      if (marcado) copia.add(clave)
      else copia.delete(clave)
      setter(copia)
    }
  }

  if (cargando) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Usuarios y Roles</h1>
          <p className="text-sm text-slate-500">
            Quién entra, con qué rol y qué puede hacer dentro de cada módulo.
          </p>
        </div>
        {/* En Inactivos no hay nada que crear: lo que se hace ahí es reactivar. */}
        {pestana !== 'inactivos' && (
          <button
            onClick={pestana === 'usuarios' ? abrirNuevoUsuario : abrirNuevoRol}
            className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <Plus size={16} />
            {pestana === 'usuarios' ? 'Nuevo usuario' : 'Nuevo rol'}
          </button>
        )}
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {(
          [
            ['usuarios', `Activos (${activos.length})`],
            ['inactivos', `Inactivos (${inactivos.length})`],
            ['roles', `Roles (${roles.length})`],
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

      {pestana !== 'roles' ? (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Correo</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {(pestana === 'usuarios' ? activos : inactivos).map((u) => {
                const soyYo = u.id === yo?.id
                return (
                  <tr key={u.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {u.nombres} {u.apellidos}
                      {soyYo && <span className="ml-2 text-xs font-normal text-slate-400">(tú)</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <Badge tone={TONO_POR_ROL[u.rol] ?? 'slate'}>{comoSeLee(u.rol)}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={u.activo ? 'green' : 'slate'}>{u.activo ? 'Activo' : 'Inactivo'}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button
                          onClick={() => abrirEdicionUsuario(u)}
                          title="Editar"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Pencil size={15} />
                        </button>
                        <button
                          onClick={() => abrirPermisos(u)}
                          title="Permisos"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <UserCog size={15} />
                        </button>
                        <button
                          onClick={() => setClaveDe(u)}
                          title="Restablecer contraseña"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <KeyRound size={15} />
                        </button>
                        {/* No hay botón de eliminar: un usuario no se borra nunca,
                            se desactiva. El porqué está en el aviso de confirmación. */}
                        {u.activo ? (
                          <button
                            onClick={() => setUsuarioAConfirmar(u)}
                            disabled={soyYo}
                            title={soyYo ? 'No puedes desactivarte a ti mismo' : 'Desactivar usuario'}
                            className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-red-300 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-200 disabled:hover:bg-white disabled:hover:text-slate-600"
                          >
                            <UserMinus size={13} /> Desactivar
                          </button>
                        ) : (
                          <button
                            onClick={() => setUsuarioAConfirmar(u)}
                            title="Volver a dar acceso"
                            className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-brand-700 hover:border-brand-300 hover:bg-brand-50"
                          >
                            <UserCheck size={13} /> Reactivar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {pestana === 'inactivos' && inactivos.length === 0 && (
            <p className="px-4 py-10 text-center text-sm text-slate-500">
              No hay usuarios inactivos. Los que desactives aparecerán aquí y podrás
              reactivarlos cuando quieras.
            </p>
          )}
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {roles.map((rol) => (
            <Card key={rol.id} className="flex h-full flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="flex items-center gap-2 font-semibold text-slate-900">
                    {comoSeLee(rol.nombre)}
                    {rol.es_sistema && (
                      <span
                        title="Rol del sistema: el código lo nombra, así que no se renombra ni se elimina"
                        className="flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-500"
                      >
                        <ShieldCheck size={11} /> sistema
                      </span>
                    )}
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {rol.descripcion || 'Sin descripción'}
                  </p>
                </div>
                <Badge tone={TONO_POR_ROL[rol.nombre] ?? 'slate'}>
                  {rol.nombre === 'super_admin' ? 'todos' : `${rol.permisos.length} permisos`}
                </Badge>
              </div>

              <p className="mt-3 flex-1 text-xs text-slate-500">
                {rol.usuarios_asignados} usuario(s) con este rol
              </p>

              <div className="mt-4 flex gap-2 border-t border-slate-100 pt-3">
                <button
                  onClick={() => abrirEdicionRol(rol)}
                  className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:border-slate-300 hover:text-slate-900"
                >
                  <Pencil size={13} /> Editar
                </button>
                <button
                  onClick={() => setRolAEliminar(rol)}
                  disabled={rol.es_sistema || rol.usuarios_asignados > 0}
                  title={
                    rol.es_sistema
                      ? 'Los roles del sistema no se eliminan'
                      : rol.usuarios_asignados > 0
                        ? 'Tiene usuarios asignados'
                        : 'Eliminar'
                  }
                  className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-red-600 hover:border-red-300 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-200 disabled:hover:bg-white"
                >
                  <Trash2 size={13} /> Eliminar
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* --------------------------------------------------- Modal de usuario */}
      <Modal
        open={modalUsuario}
        onClose={() => setModalUsuario(false)}
        title={usuarioEnEdicion ? `Editar: ${usuarioEnEdicion.nombres}` : 'Nuevo usuario'}
        confirmarCierre="Se perderá lo que hayas escrito."
      >
        <form onSubmit={guardarUsuario} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Nombres *</label>
              <input
                required
                value={formUsuario.nombres}
                onChange={(e) => setFormUsuario({ ...formUsuario, nombres: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Apellidos *</label>
              <input
                required
                value={formUsuario.apellidos}
                onChange={(e) => setFormUsuario({ ...formUsuario, apellidos: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Correo *</label>
            <input
              type="email"
              required
              value={formUsuario.email}
              onChange={(e) => setFormUsuario({ ...formUsuario, email: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {!usuarioEnEdicion && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Contraseña *</label>
              <input
                type="password"
                required
                minLength={8}
                value={formUsuario.password}
                onChange={(e) => setFormUsuario({ ...formUsuario, password: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <p className="mt-1 text-xs text-slate-500">
                Mínimo 8 caracteres. Pásasela por un canal seguro; el sistema no la vuelve a mostrar.
              </p>
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Rol *</label>
            <select
              required
              value={formUsuario.rol}
              onChange={(e) => setFormUsuario({ ...formUsuario, rol: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              {rolesActivos.map((r) => (
                <option key={r.id} value={r.nombre}>
                  {comoSeLee(r.nombre)}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={guardando}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {guardando && <Loader2 size={15} className="animate-spin" />}
            {usuarioEnEdicion ? 'Guardar cambios' : 'Crear usuario'}
          </button>
        </form>
      </Modal>

      {/* ------------------------------------------------ Modal de contraseña */}
      <Modal open={claveDe !== null} onClose={() => setClaveDe(null)} title="Restablecer contraseña">
        <form onSubmit={guardarClave} className="space-y-4">
          <p className="text-sm text-slate-600">
            Nueva contraseña para <strong>{claveDe?.nombres} {claveDe?.apellidos}</strong>.
          </p>
          <input
            type="password"
            required
            minLength={8}
            value={claveNueva}
            onChange={(e) => setClaveNueva(e.target.value)}
            placeholder="Mínimo 8 caracteres"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <p className="text-xs text-slate-500">
            El sistema no guarda la contraseña en claro ni la vuelve a mostrar: cópiala ahora y
            pásasela por un canal seguro.
          </p>
          <button
            type="submit"
            disabled={guardando}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {guardando && <Loader2 size={15} className="animate-spin" />}
            Cambiar contraseña
          </button>
        </form>
      </Modal>

      {/* -------------------------------------------- Modal de permisos de usuario */}
      <Modal
        open={permisosDe !== null}
        onClose={() => setPermisosDe(null)}
        title={`Permisos de ${permisosDe?.nombres ?? ''}`}
        wide
      >
        {!detallePermisos ? (
          <div className="flex justify-center py-10 text-slate-400">
            <Loader2 className="animate-spin" />
          </div>
        ) : detallePermisos.es_super_admin ? (
          <div className="rounded-lg bg-slate-50 p-5 text-center">
            <ShieldCheck className="mx-auto text-brand-600" size={28} />
            <p className="mt-3 text-sm font-medium text-slate-800">Super admin: lo puede todo</p>
            <p className="mt-1 text-sm text-slate-500">
              No admite ajustes a propósito. Si se le pudieran quitar permisos, alguien podría
              dejarse fuera de su propio sistema sin forma de volver a entrar.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="rounded-lg bg-brand-50 p-3 text-sm text-brand-900">
              Las casillas marcadas son lo que <strong>puede hacer de verdad</strong>. Vienen de su
              rol <strong>{comoSeLee(detallePermisos.rol)}</strong>; lo que cambies aquí queda como
              excepción solo para esta persona.
            </p>

            <SelectorDePermisos
              catalogo={catalogo}
              seleccionados={permisosElegidos}
              heredados={new Set(detallePermisos.del_rol)}
              onToggle={alternar(permisosElegidos, setPermisosElegidos)}
            />

            <button
              type="button"
              onClick={guardarPermisos}
              disabled={guardando}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {guardando && <Loader2 size={15} className="animate-spin" />}
              Guardar permisos
            </button>
          </div>
        )}
      </Modal>

      {/* ------------------------------------------------------- Modal de rol */}
      <Modal
        open={modalRol}
        onClose={() => setModalRol(false)}
        title={rolEnEdicion ? `Editar rol: ${comoSeLee(rolEnEdicion.nombre)}` : 'Nuevo rol'}
        wide
        confirmarCierre="Se perderá lo que hayas escrito."
      >
        <form onSubmit={guardarRol} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Nombre *</label>
            <input
              required
              value={formRol.nombre}
              disabled={rolEnEdicion?.es_sistema}
              onChange={(e) => setFormRol({ ...formRol, nombre: e.target.value })}
              placeholder="Coordinador de selección"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-50 disabled:text-slate-500"
            />
            <p className="mt-1 text-xs text-slate-500">
              {rolEnEdicion?.es_sistema
                ? 'Los roles del sistema no se renombran: el código los nombra y cambiarlo dejaría pantallas sin acceso. Sus permisos sí se pueden ajustar.'
                : 'Se guarda en minúsculas y con guiones bajos, porque se usa como identificador.'}
            </p>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Descripción</label>
            <textarea
              rows={2}
              value={formRol.descripcion}
              onChange={(e) => setFormRol({ ...formRol, descripcion: e.target.value })}
              placeholder="Qué hace esta persona en el sistema."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Permisos</label>
            {rolEnEdicion?.nombre === 'super_admin' ? (
              <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                El super admin tiene todos los permisos por definición y no admite ajustes.
              </p>
            ) : (
              <SelectorDePermisos
                catalogo={catalogo}
                seleccionados={permisosDelRol}
                onToggle={alternar(permisosDelRol, setPermisosDelRol)}
              />
            )}
          </div>

          <button
            type="submit"
            disabled={guardando}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {guardando && <Loader2 size={15} className="animate-spin" />}
            {rolEnEdicion ? 'Guardar cambios' : 'Crear rol'}
          </button>
        </form>
      </Modal>

      {/* ------------------------------------------------------ Confirmaciones */}
      <Modal
        open={usuarioAConfirmar !== null}
        onClose={() => setUsuarioAConfirmar(null)}
        title={usuarioAConfirmar?.activo ? 'Desactivar usuario' : 'Reactivar usuario'}
      >
        <div className="space-y-5">
          {usuarioAConfirmar?.activo ? (
            <>
              <p className="text-sm text-slate-600">
                <strong>
                  {usuarioAConfirmar?.nombres} {usuarioAConfirmar?.apellidos}
                </strong>{' '}
                dejará de poder entrar al sistema. Pasará a la pestaña{' '}
                <strong>Inactivos</strong>, desde donde puedes reactivarlo cuando quieras con su
                mismo rol y sus mismos permisos.
              </p>

              {/* Por qué no hay un botón de eliminar. Es la pregunta que se hace
                  cualquiera al no encontrarlo, y merece respuesta aquí y no en un manual. */}
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-sm font-medium text-slate-700">
                  ¿Por qué no se puede eliminar?
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  Porque esta persona es la <strong>autora</strong> de lo que hizo: las vacantes
                  que publicó y las evaluaciones que puso llevan su nombre. Borrarla dejaría esos
                  registros sin autor y abriría huecos en el historial de procesos de selección
                  que luego hay que poder reconstruir —por ejemplo, para explicar por qué se
                  contrató a quien se contrató.
                </p>
                <p className="mt-2 text-sm text-slate-600">
                  Desactivar consigue lo mismo que te interesa —que no entre— sin perder nada.
                </p>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-600">
              <strong>
                {usuarioAConfirmar?.nombres} {usuarioAConfirmar?.apellidos}
              </strong>{' '}
              volverá a poder entrar con su rol y permisos anteriores, y saldrá de la pestaña de
              inactivos.
            </p>
          )}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setUsuarioAConfirmar(null)}
              className="flex-1 rounded-lg border border-slate-300 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmarCambioDeEstado}
              disabled={guardando}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium text-white disabled:opacity-60 ${
                usuarioAConfirmar?.activo
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-brand-600 hover:bg-brand-700'
              }`}
            >
              {guardando && <Loader2 size={15} className="animate-spin" />}
              {usuarioAConfirmar?.activo ? 'Sí, desactivar' : 'Sí, reactivar'}
            </button>
          </div>
        </div>
      </Modal>

      <Modal open={rolAEliminar !== null} onClose={() => setRolAEliminar(null)} title="Eliminar rol">
        <div className="space-y-5">
          <p className="text-sm text-slate-600">
            ¿Seguro que quieres eliminar <strong>{comoSeLee(rolAEliminar?.nombre ?? '')}</strong>?
            Esto sí borra el rol; no hay usuarios asignados, así que no deja a nadie sin acceso.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setRolAEliminar(null)}
              className="flex-1 rounded-lg border border-slate-300 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={confirmarEliminarRol}
              disabled={guardando}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-600 py-2.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
            >
              {guardando && <Loader2 size={15} className="animate-spin" />}
              Sí, eliminar
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
