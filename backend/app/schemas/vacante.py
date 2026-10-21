from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.vacante import ESTADOS, ESTADOS_DEL_POST, VISIBILIDADES
from app.schemas.cargo import PreguntaFiltroOut

MAXIMO_CAMPOS_PERSONALIZADOS = 20


class CampoPersonalizado(BaseModel):
    etiqueta: str = Field(max_length=100)
    valor: str = Field(default="", max_length=500)

    @field_validator("etiqueta")
    @classmethod
    def etiqueta_con_contenido(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("La etiqueta del campo no puede estar vacía")
        return limpio


class VacanteCreate(BaseModel):
    """El título no está: sale del cargo. Ver el comentario del modelo."""

    cargo_id: int
    descripcion: str
    fecha_limite: datetime

    remuneracion: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    jornada_horas: Decimal | None = Field(default=None, gt=0, le=24, max_digits=4, decimal_places=2)
    hora_entrada: time | None = None
    hora_salida: time | None = None
    tipo_contrato_id: int | None = None
    campos_personalizados: list[CampoPersonalizado] = []

    asunto: str | None = Field(default=None, max_length=200)
    post_cuerpo: str | None = None
    post_imagen_url: str | None = Field(default=None, max_length=500)
    post_programado_para: datetime | None = None

    estado: str = "borrador"
    visibilidad: str = "publica"
    destinatarios_internos: list[EmailStr] = []

    @field_validator("estado")
    @classmethod
    def estado_conocido(cls, v: str) -> str:
        if v not in ESTADOS:
            raise ValueError(f"Estado inválido: {v}. Debe ser uno de {', '.join(ESTADOS)}")
        return v

    @field_validator("visibilidad")
    @classmethod
    def visibilidad_conocida(cls, v: str) -> str:
        if v not in VISIBILIDADES:
            raise ValueError(f"Visibilidad inválida: {v}. Debe ser una de {', '.join(VISIBILIDADES)}")
        return v

    @field_validator("campos_personalizados")
    @classmethod
    def campos_sin_repetir_y_con_tope(cls, v: list[CampoPersonalizado]) -> list[CampoPersonalizado]:
        if len(v) > MAXIMO_CAMPOS_PERSONALIZADOS:
            raise ValueError(f"Como mucho {MAXIMO_CAMPOS_PERSONALIZADOS} campos personalizados")
        vistas = [c.etiqueta.strip().lower() for c in v]
        if len(vistas) != len(set(vistas)):
            raise ValueError("Hay dos campos personalizados con la misma etiqueta")
        return v

    @model_validator(mode="after")
    def coherencia(self):
        if self.hora_entrada and self.hora_salida and self.hora_entrada == self.hora_salida:
            raise ValueError("La hora de entrada y la de salida no pueden ser la misma")
        # Una vacante interna sin destinatarios no llega a nadie: es un error de uso,
        # no un caso válido que convenga dejar pasar en silencio.
        if self.visibilidad in ("interna", "mixta") and not self.destinatarios_internos:
            raise ValueError("Una vacante interna o mixta necesita al menos un correo destinatario")
        if self.post_programado_para and self.post_programado_para <= datetime.now(self.post_programado_para.tzinfo):
            raise ValueError("La fecha de publicación programada ya pasó")
        return self


def calcular_hora_de_salida(entrada: time, horas: Decimal) -> time:
    """Entrada + jornada, dando la vuelta al reloj si cruza la medianoche."""
    base = datetime(2000, 1, 1, entrada.hour, entrada.minute)
    return (base + timedelta(hours=float(horas))).time()


class VacanteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cargo_id: int
    titulo: str
    descripcion: str
    slug: str
    fecha_limite: datetime

    remuneracion: Decimal | None
    jornada_horas: Decimal | None
    hora_entrada: time | None
    hora_salida: time | None
    tipo_contrato_id: int | None
    # Nombre resuelto. Se llama distinto que la relación del modelo a propósito:
    # `model_validate` mapea por nombre y tomaría el objeto ORM en lugar del texto.
    tipo_contrato_nombre: str | None = None
    campos_personalizados: list[CampoPersonalizado]

    asunto: str | None
    post_cuerpo: str | None
    post_imagen_url: str | None
    post_programado_para: datetime | None
    post_estado: str
    post_publicado_en: datetime | None
    post_error: str | None
    linkedin_post_id: str | None

    visibilidad: str
    destinatarios_internos: list[str]
    enviado_internamente_en: datetime | None

    url_publica: str | None = None
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
    remuneracion: Decimal | None = None
    hora_entrada: time | None = None
    hora_salida: time | None = None
    tipo_contrato: str | None = None
    campos_personalizados: list[CampoPersonalizado] = []
    preguntas_filtro: list[PreguntaFiltroOut] = []


class CambioDeEstado(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def estado_conocido(cls, v: str) -> str:
        if v not in ESTADOS:
            raise ValueError(f"Estado inválido: {v}. Debe ser uno de {', '.join(ESTADOS)}")
        return v


class CambioDeEstadoDelPost(BaseModel):
    post_estado: str

    @field_validator("post_estado")
    @classmethod
    def estado_conocido(cls, v: str) -> str:
        if v not in ESTADOS_DEL_POST:
            raise ValueError(f"Estado de post inválido: {v}. Debe ser uno de {', '.join(ESTADOS_DEL_POST)}")
        return v


class VistaPreviaDelPost(BaseModel):
    """Cómo se verá el post antes de publicarlo, y por dónde puede salir."""

    asunto: str
    cuerpo: str
    imagen_url: str | None
    enlace_para_postular: str
    visibilidad: str
    destinatarios_internos: list[str]
    programado_para: datetime | None
    caracteres: int


class ResultadoDePublicacion(BaseModel):
    post_estado: str
    linkedin_post_id: str | None = None
    simulado: bool = False
    mensaje: str


class EnvioInternoOut(BaseModel):
    enviados: int
    mensaje: str


class ImagenSubidaOut(BaseModel):
    url: str


class LinkedInPublishOut(BaseModel):
    linkedin_post_id: str


class WhatsAppShareOut(BaseModel):
    whatsapp_url: str
