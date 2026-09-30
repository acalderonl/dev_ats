from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluacionCreate(BaseModel):
    tipo_evaluacion: str
    puntaje: float = Field(ge=0, le=100)
    observaciones: str | None = None


class EvaluacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    postulacion_id: UUID
    evaluador_id: UUID
    tipo_evaluacion: str
    puntaje: float | None
    observaciones: str | None
    creado_en: datetime
