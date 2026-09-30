from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioActivoUpdate, UsuarioOut, UsuarioRolUpdate

router = APIRouter()


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> list[UsuarioOut]:
    usuarios = db.scalars(select(Usuario)).all()
    return [UsuarioOut.from_orm_with_rol(u) for u in usuarios]


@router.put("/{user_id}/role", response_model=UsuarioOut)
def actualizar_rol(
    user_id: UUID,
    payload: UsuarioRolUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> UsuarioOut:
    usuario = db.get(Usuario, user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    rol = db.scalar(select(Rol).where(Rol.nombre == payload.rol))
    if rol is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido")

    usuario.rol_id = rol.id
    db.commit()
    db.refresh(usuario)
    return UsuarioOut.from_orm_with_rol(usuario)


@router.patch("/{user_id}/activo", response_model=UsuarioOut)
def actualizar_estado(
    user_id: UUID,
    payload: UsuarioActivoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> UsuarioOut:
    usuario = db.get(Usuario, user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    usuario.activo = payload.activo
    db.commit()
    db.refresh(usuario)
    return UsuarioOut.from_orm_with_rol(usuario)
