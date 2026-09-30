from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

RolNombre = str  # 'super_admin' | 'reclutador' | 'entrevistador'


class UsuarioRegistro(BaseModel):
    email: EmailStr
    password: str
    nombres: str
    apellidos: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombres: str
    apellidos: str
    rol: str
    activo: bool
    creado_en: datetime

    @classmethod
    def from_orm_with_rol(cls, usuario) -> "UsuarioOut":
        return cls(
            id=usuario.id,
            email=usuario.email,
            nombres=usuario.nombres,
            apellidos=usuario.apellidos,
            rol=usuario.rol.nombre,
            activo=usuario.activo,
            creado_en=usuario.creado_en,
        )


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioOut


class UsuarioRolUpdate(BaseModel):
    rol: str


class UsuarioActivoUpdate(BaseModel):
    activo: bool
