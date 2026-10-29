import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Un nombre de rol se usa como identificador en el código y en la API, así que se
# normaliza: minúsculas, sin espacios y sin tildes.
PATRON_DE_NOMBRE = re.compile(r"^[a-z][a-z0-9_]{2,49}$")


class PermisoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clave: str
    modulo: str
    accion: str
    etiqueta: str


class RolCreate(BaseModel):
    nombre: str = Field(max_length=50)
    descripcion: str | None = None
    permisos: list[str] = Field(default=[], description="Claves de permiso, p. ej. vacantes.crear")

    @field_validator("nombre")
    @classmethod
    def nombre_utilizable(cls, v: str) -> str:
        limpio = v.strip().lower().replace(" ", "_").replace("-", "_")
        if not PATRON_DE_NOMBRE.match(limpio):
            raise ValueError(
                "El nombre del rol debe empezar por una letra y llevar solo letras, "
                "números o guiones bajos (entre 3 y 50 caracteres)"
            )
        return limpio


class RolUpdate(BaseModel):
    """Todo opcional: se actualiza lo que venga."""

    nombre: str | None = Field(default=None, max_length=50)
    descripcion: str | None = None
    activo: bool | None = None
    permisos: list[str] | None = None

    @field_validator("nombre")
    @classmethod
    def nombre_utilizable(cls, v: str | None) -> str | None:
        return RolCreate.nombre_utilizable(v) if v is not None else None


class RolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    es_sistema: bool
    activo: bool
    permisos: list[str] = []
    usuarios_asignados: int = 0
