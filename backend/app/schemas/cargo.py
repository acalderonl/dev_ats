from typing import Literal

from pydantic import BaseModel, ConfigDict

TipoRespuesta = Literal["multiple", "unica", "texto", "booleano", "numero"]


class CargoCreate(BaseModel):
    nombre: str
    departamento: str | None = None
    descripcion: str | None = None


class CargoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    departamento: str | None
    descripcion: str | None
    activo: bool


class PreguntaFiltroCreate(BaseModel):
    pregunta: str
    tipo_respuesta: TipoRespuesta
    opciones: list[str] | None = None
    es_eliminatoria: bool = False
    respuesta_correcta: str | None = None


class PreguntaFiltroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cargo_id: int
    pregunta: str
    tipo_respuesta: str
    opciones: list[str] | None
    es_eliminatoria: bool
    respuesta_correcta: str | None
