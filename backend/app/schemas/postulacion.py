from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

EstadoPipeline = Literal[
    "pendiente_autorizacion",
    "postulacion_revisada",
    "en_revision",
    "preseleccionado",
    "evaluaciones",
    "entrevista",
    "contratado",
    "descartado",
]


class PostulacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # A qué convocatoria se postuló. `vacante_id` se deriva de ella y se mantiene
    # porque el pipeline agrupa por vacante, no por ronda.
    convocatoria_id: UUID
    convocatoria_numero: int
    vacante_id: UUID
    postulante_id: UUID
    respuestas_filtro: dict | None
    autorizado_por: UUID | None
    fecha_autorizacion: datetime | None
    estado_pipeline: str
    origen: str
    match_score: float | None
    creado_en: datetime
    postulante_nombres: str
    postulante_apellidos: str
    vacante_titulo: str

    @classmethod
    def from_orm_enriquecido(cls, postulacion) -> "PostulacionOut":
        convocatoria = postulacion.convocatoria
        return cls(
            id=postulacion.id,
            convocatoria_id=postulacion.convocatoria_id,
            convocatoria_numero=convocatoria.numero,
            vacante_id=convocatoria.vacante_id,
            postulante_id=postulacion.postulante_id,
            respuestas_filtro=postulacion.respuestas_filtro,
            autorizado_por=postulacion.autorizado_por,
            fecha_autorizacion=postulacion.fecha_autorizacion,
            estado_pipeline=postulacion.estado_pipeline,
            origen=postulacion.origen,
            match_score=float(postulacion.match_score) if postulacion.match_score is not None else None,
            creado_en=postulacion.creado_en,
            postulante_nombres=postulacion.postulante.nombres,
            postulante_apellidos=postulacion.postulante.apellidos,
            vacante_titulo=convocatoria.vacante.titulo,
        )


class PipelineStatusUpdate(BaseModel):
    estado_pipeline: EstadoPipeline
