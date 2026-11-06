"""CRUD de roles y catálogo de permisos.

Los tres roles iniciales están **protegidos contra renombrado y borrado**. No es
burocracia: el código todavía los nombra en `require_roles("super_admin", ...)`, así
que renombrar `reclutador` dejaría esos endpoints sin dejar pasar a nadie y sin ningún
error visible. Sus permisos sí se pueden ajustar, que es lo que se querría cambiar en
la práctica.

Un rol con usuarios asignados tampoco se borra: dejaría esas cuentas apuntando a una
fila que no existe. Hay que moverlas antes, y el error lo dice con el número.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permisos import ROL_TODOPODEROSO, require_permission
from app.models.permiso import Permiso, RolPermiso
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.rol import PermisoOut, RolCreate, RolOut, RolUpdate

router = APIRouter()


def _a_salida(db: Session, rol: Rol) -> RolOut:
    claves = db.scalars(
        select(Permiso.clave)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == rol.id)
        .order_by(Permiso.orden)
    ).all()
    asignados = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.rol_id == rol.id)) or 0
    return RolOut(
        id=rol.id,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        es_sistema=rol.es_sistema,
        activo=rol.activo,
        permisos=list(claves),
        usuarios_asignados=asignados,
    )


def _rol_o_404(db: Session, rol_id: int) -> Rol:
    rol = db.get(Rol, rol_id)
    if rol is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    return rol


def _guardar_permisos(db: Session, rol: Rol, claves: list[str]) -> None:
    por_clave = {p.clave: p for p in db.scalars(select(Permiso)).all()}
    desconocidas = [c for c in claves if c not in por_clave]
    if desconocidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permisos desconocidos: {', '.join(desconocidas)}",
        )
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol.id).delete()
    for clave in claves:
        db.add(RolPermiso(rol_id=rol.id, permiso_id=por_clave[clave].id))


@router.get("/permisos", response_model=list[PermisoOut])
def listar_permisos(
    db: Session = Depends(get_db), _: Usuario = Depends(require_permission("usuarios.ver"))
) -> list[PermisoOut]:
    """El catálogo completo. La pantalla lo agrupa por módulo para pintar las casillas."""
    return db.scalars(select(Permiso).order_by(Permiso.orden)).all()


@router.get("", response_model=list[RolOut])
def listar_roles(
    db: Session = Depends(get_db), _: Usuario = Depends(require_permission("usuarios.ver"))
) -> list[RolOut]:
    roles = db.scalars(select(Rol).order_by(Rol.es_sistema.desc(), Rol.nombre)).all()
    return [_a_salida(db, r) for r in roles]


@router.post("", response_model=RolOut, status_code=status.HTTP_201_CREATED)
def crear_rol(
    payload: RolCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.gestionar_roles")),
) -> RolOut:
    rol = Rol(nombre=payload.nombre, descripcion=payload.descripcion, es_sistema=False, activo=True)
    db.add(rol)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe un rol llamado '{payload.nombre}'")
    _guardar_permisos(db, rol, payload.permisos)
    db.commit()
    db.refresh(rol)
    return _a_salida(db, rol)


@router.put("/{rol_id}", response_model=RolOut)
def actualizar_rol(
    rol_id: int,
    payload: RolUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.gestionar_roles")),
) -> RolOut:
    rol = _rol_o_404(db, rol_id)
    datos = payload.model_dump(exclude_unset=True)
    permisos = datos.pop("permisos", None)

    if rol.es_sistema:
        if "nombre" in datos and datos["nombre"] != rol.nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{rol.nombre}' es un rol del sistema y su nombre está referenciado en el código. "
                "Puedes cambiar su descripción y sus permisos, pero no cómo se llama.",
            )
        if datos.get("activo") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{rol.nombre}' es un rol del sistema y no se puede desactivar.",
            )
        datos.pop("nombre", None)

    if rol.nombre == ROL_TODOPODEROSO and permisos is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El super admin tiene todos los permisos por definición y no admite ajustes.",
        )

    for campo, valor in datos.items():
        setattr(rol, campo, valor)
    if permisos is not None:
        _guardar_permisos(db, rol, permisos)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de rol ya está en uso")
    db.refresh(rol)
    return _a_salida(db, rol)


@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_permission("usuarios.gestionar_roles")),
) -> None:
    rol = _rol_o_404(db, rol_id)
    if rol.es_sistema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{rol.nombre}' es un rol del sistema y no se puede eliminar.",
        )

    asignados = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.rol_id == rol.id)) or 0
    if asignados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{asignados} usuario(s) tienen este rol. Cámbialos de rol antes de eliminarlo.",
        )

    db.delete(rol)
    db.commit()
