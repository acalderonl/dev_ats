from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import TokenOut, UsuarioLogin, UsuarioOut, UsuarioRegistro

router = APIRouter()


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def register(payload: UsuarioRegistro, db: Session = Depends(get_db)) -> UsuarioOut:
    existing = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")

    rol = db.scalar(select(Rol).where(Rol.nombre == "reclutador"))
    if rol is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Rol 'reclutador' no configurado")

    usuario = Usuario(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        rol_id=rol.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return UsuarioOut.from_orm_with_rol(usuario)


@router.post("/login", response_model=TokenOut)
def login(payload: UsuarioLogin, db: Session = Depends(get_db)) -> TokenOut:
    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if usuario is None or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not usuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    token = create_access_token(subject=str(usuario.id))
    return TokenOut(access_token=token, user=UsuarioOut.from_orm_with_rol(usuario))


@router.get("/me", response_model=UsuarioOut)
def me(current_user: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut.from_orm_with_rol(current_user)
