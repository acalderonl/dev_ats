from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.cargo import PreguntaFiltroOut


class VacanteCreate(BaseModel):
    titulo: str
    cargo_id: int
    descripcion: str
    fecha_limite: datetime


class VacanteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    cargo_id: int
    descripcion: str
    documento_adjunto_url: str | None
    slug: str
    fecha_limite: datetime
    linkedin_post_id: str | None
    empleador_id: UUID
    estado: str
    creado_en: datetime


class VacantePublicaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descripcion: str
    slug: str
    fecha_limite: datetime
    cargo_nombre: str
    preguntas_filtro: list[PreguntaFiltroOut] = []


class LinkedInPublishOut(BaseModel):
    linkedin_post_id: str


class WhatsAppShareOut(BaseModel):
    whatsapp_url: str
