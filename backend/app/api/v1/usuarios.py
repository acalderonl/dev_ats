"""Administración de usuarios.

**Nadie se borra.** Un usuario que publicó vacantes o evaluó candidatos es el autor de
esos registros; eliminarlo dejaría huecos en el historial de un proceso de selección,
que es justo lo que hay que poder reconstruir si alguien pregunta por qué se contrató
a quien se contrató. En su lugar se desactiva: deja de entrar y su rastro se conserva.

Tres cosas que el código impide a propósito, todas variantes del mismo accidente —
quedarse fuera del propio sistema:

- desactivarse a uno mismo,
- quitarse a uno mismo el rol de super admin,
- dejar la aplicación sin ningún super admin activo.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permisos import ROL_TODOPODEROSO, permisos_de, require_permission
from app.core.security import get_current_user, hash_password
from app.models.permiso import Permiso, RolPermiso, UsuarioPermiso
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import (
    AjusteDePermiso,
    CambioDeClave,
    PermisosDeUsuario,
    UsuarioActivoUpdate,
    UsuarioCreate,
    UsuarioOut,
    UsuarioRolUpdate,
    UsuarioUpdate,
)

router = APIRouter()


# Va antes que las rutas con `{user_id}`: FastAPI resuelve por orden de declaración y
# "yo" no es un UUID, así que declarada después devolvería un 422 en vez de entrar.
@router.get("/yo/permisos", response_model=list[str])
def mis_permisos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)) -> list[str]:
    """Los permisos de quien pregunta. La usa el frontend para pintar el menú."""
    return sorted(permisos_de(db, usuario))


def _usuario_o_404(db: Session, user_id: UUID) -> Usuario:
    usuario = db.get(Usuario, user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def _rol_o_400(db: Session, nombre: str) -> Rol:
    rol = db.scalar(select(Rol).where(Rol.nombre == nombre))
    if rol is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El rol '{nombre}' no existe")
    if not rol.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El rol '{nombre}' está desactivado")
    return rol


def _quedan_super_admins(db: Session, excluyendo: UUID) -> bool:
    """¿Queda algún super admin activo aparte de este?"""
    total = db.scalar(
        select(func.count())
        .select_from(Usuario)
        .join(Rol, Rol.id == Usuario.rol_id)
        .where(Rol.nombre == ROL_TODOPODEROSO, Usuario.activo.is_(True), Usuario.id != excluyendo)
    )
    return (total or 0) > 0


def _proteger_ultimo_super_admin(db: Session, usuario: Usuario) -> None:
    if usuario.rol.nombre == ROL_TODOPODEROSO and not _quedan_super_admins(db, usuario.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Es el único super admin activo. Nombra otro antes de quitarle el acceso.",
        )


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db), _: Usuario = Depends(require_permission("usuarios.ver"))
) -> list[UsuarioOut]:
    usuarios = db.scalars(select(Usuario).order_by(Usuario.creado_en)).all()
    return [UsuarioOut.from_orm_with_rol(u) for u in usuarios]


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.crear")),
) -> UsuarioOut:
    rol = _rol_o_400(db, payload.rol)
    usuario = Usuario(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        rol_id=rol.id,
        activo=payload.activo,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe un usuario con el correo {payload.email}"
        )
    db.refresh(usuario)
    return UsuarioOut.from_orm_with_rol(usuario)


@router.put("/{user_id}", response_model=UsuarioOut)
def actualizar_usuario(
    user_id: UUID,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_permission("usuarios.editar")),
) -> UsuarioOut:
    usuario = _usuario_o_404(db, user_id)
    datos = payload.model_dump(exclude_unset=True)

    nuevo_rol = datos.pop("rol", None)
    if nuevo_rol is not None and nuevo_rol != usuario.rol.nombre:
        if usuario.id == actual.id and usuario.rol.nombre == ROL_TODOPODEROSO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes quitarte a ti mismo el rol de super admin.",
            )
        _proteger_ultimo_super_admin(db, usuario)
        usuario.rol_id = _rol_o_400(db, nuevo_rol).id

    if datos.get("activo") is False:
        if usuario.id == actual.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes desactivarte a ti mismo.")
        _proteger_ultimo_super_admin(db, usuario)

    for campo, valor in datos.items():
        setattr(usuario, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está en uso")
    db.refresh(usuario)
    return UsuarioOut.from_orm_with_rol(usuario)


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def restablecer_clave(
    user_id: UUID,
    payload: CambioDeClave,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.editar")),
) -> None:
    """Pone una contraseña nueva. No se devuelve ni se guarda en claro en ningún sitio."""
    usuario = _usuario_o_404(db, user_id)
    usuario.password_hash = hash_password(payload.password)
    db.commit()


@router.put("/{user_id}/role", response_model=UsuarioOut)
def actualizar_rol(
    user_id: UUID,
    payload: UsuarioRolUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_permission("usuarios.asignar_rol")),
) -> UsuarioOut:
    return actualizar_usuario(user_id=user_id, payload=UsuarioUpdate(rol=payload.rol), db=db, actual=actual)


@router.patch("/{user_id}/activo", response_model=UsuarioOut)
def actualizar_estado(
    user_id: UUID,
    payload: UsuarioActivoUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_permission("usuarios.cambiar_estado")),
) -> UsuarioOut:
    """Desactivar es lo que hace el botón de eliminar: el rastro del usuario se conserva."""
    return actualizar_usuario(user_id=user_id, payload=UsuarioUpdate(activo=payload.activo), db=db, actual=actual)


# ------------------------------------------------------------------- Permisos


@router.get("/{user_id}/permisos", response_model=PermisosDeUsuario)
def permisos_del_usuario(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.asignar_rol")),
) -> PermisosDeUsuario:
    usuario = _usuario_o_404(db, user_id)

    del_rol = db.scalars(
        select(Permiso.clave)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == usuario.rol_id)
    ).all()
    ajustes = db.execute(
        select(Permiso.clave, UsuarioPermiso.concedido)
        .join(UsuarioPermiso, UsuarioPermiso.permiso_id == Permiso.id)
        .where(UsuarioPermiso.usuario_id == usuario.id)
    ).all()

    return PermisosDeUsuario(
        rol=usuario.rol.nombre,
        es_super_admin=usuario.rol.nombre == ROL_TODOPODEROSO,
        del_rol=sorted(del_rol),
        ajustes={clave: concedido for clave, concedido in ajustes},
        efectivos=sorted(permisos_de(db, usuario)),
    )


@router.put("/{user_id}/permisos", response_model=PermisosDeUsuario)
def ajustar_permisos(
    user_id: UUID,
    ajustes: list[AjusteDePermiso],
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.asignar_rol")),
) -> PermisosDeUsuario:
    """Reemplaza las excepciones de este usuario respecto a su rol.

    Solo se mandan las diferencias: un permiso que coincide con lo que da el rol no
    necesita fila. Así, si mañana cambia la plantilla del rol, los usuarios la heredan
    en vez de quedarse congelados con una copia.
    """
    usuario = _usuario_o_404(db, user_id)
    if usuario.rol.nombre == ROL_TODOPODEROSO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un super admin tiene todos los permisos y no admite ajustes.",
        )

    por_clave = {p.clave: p for p in db.scalars(select(Permiso)).all()}
    desconocidas = [a.clave for a in ajustes if a.clave not in por_clave]
    if desconocidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permisos desconocidos: {', '.join(desconocidas)}",
        )

    db.query(UsuarioPermiso).filter(UsuarioPermiso.usuario_id == usuario.id).delete()
    for ajuste in ajustes:
        db.add(UsuarioPermiso(usuario_id=usuario.id, permiso_id=por_clave[ajuste.clave].id, concedido=ajuste.concedido))
    db.commit()
    return permisos_del_usuario(user_id=user_id, db=db, _=usuario)
