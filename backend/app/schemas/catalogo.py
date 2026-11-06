from pydantic import BaseModel, ConfigDict, field_validator


class CatalogoCreate(BaseModel):
    nombre: str

    @field_validator("nombre")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío")
        return limpio


class CatalogoUpdate(BaseModel):
    nombre: str | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def no_vacio(cls, v: str | None) -> str | None:
        if v is None:
            return v
        limpio = v.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío")
        return limpio


class CatalogoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool
    en_uso: bool = False
