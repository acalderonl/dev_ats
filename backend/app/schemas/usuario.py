from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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


LARGO_MINIMO_DE_CLAVE = 8


def _clave_utilizable(v: str) -> str:
    """Un mínimo razonable y nada más.

    No se exigen símbolos ni mayúsculas: esas reglas empujan a la gente a escribir
    `Empresa2026!` y a apuntarlo en un papel. La longitud es lo que de verdad cuesta
    de romper.
    """
    if len(v) < LARGO_MINIMO_DE_CLAVE:
        raise ValueError(f"La contraseña debe tener al menos {LARGO_MINIMO_DE_CLAVE} caracteres")
    return v


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombres: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=100)
    password: str
    rol: str
    activo: bool = True

    @field_validator("password")
    @classmethod
    def clave_valida(cls, v: str) -> str:
        return _clave_utilizable(v)


class UsuarioUpdate(BaseModel):
    """Lo que un administrador puede cambiar. La contraseña va por su propio endpoint."""

    email: EmailStr | None = None
    nombres: str | None = Field(default=None, min_length=1, max_length=100)
    apellidos: str | None = Field(default=None, min_length=1, max_length=100)
    rol: str | None = None
    activo: bool | None = None


class CambioDeClave(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def clave_valida(cls, v: str) -> str:
        return _clave_utilizable(v)


class AjusteDePermiso(BaseModel):
    clave: str
    concedido: bool


class PermisosDeUsuario(BaseModel):
    """Lo que la pantalla necesita para pintar las casillas sin adivinar nada."""

    rol: str
    es_super_admin: bool
    # Lo que trae su rol de fábrica.
    del_rol: list[str]
    # Las excepciones que se le pusieron: clave -> concedido.
    ajustes: dict[str, bool]
    # El resultado de aplicar unas sobre otras: lo que de verdad puede hacer.
    efectivos: list[str]
