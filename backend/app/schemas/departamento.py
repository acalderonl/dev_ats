from pydantic import BaseModel, ConfigDict, Field, field_validator


class DepartamentoCreate(BaseModel):
    nombre: str = Field(max_length=120)
    descripcion: str | None = None

    @field_validator("nombre")
    @classmethod
    def con_contenido(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("El nombre del departamento no puede estar vacío")
        return limpio


class DepartamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None
    activo: bool
    # «Sin asignar»: no se renombra ni se desactiva. La pantalla esconde esos botones.
    es_sistema: bool
    # Cuántos cargos cuelgan de él. La UI lo enseña y decide si avisar al desactivar.
    cargos: int = 0
