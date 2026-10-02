from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.cargo import TipoCompetencia


class CompetenciaCreate(BaseModel):
    nombre: str
    tipo: TipoCompetencia

    @field_validator("nombre")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        limpio = " ".join(v.split())
        if not limpio:
            raise ValueError("El nombre no puede estar vacío")
        return limpio


class CompetenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: str
    activo: bool
    # Cuántos cargos la usan: ayuda a elegir la que ya está establecida en vez de crear otra.
    usos: int = 0
    # 0 a 1. Solo viene al buscar: cuánto se parece a lo que se escribió.
    similitud: float | None = None
