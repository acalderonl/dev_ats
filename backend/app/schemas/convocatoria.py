from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.convocatoria import ESTADOS, ESTADOS_DEL_POST


class ConvocatoriaCreate(BaseModel):
    """El ciclo: hasta cuándo, en qué estado, y con qué post se anuncia.

    Las condiciones del puesto no están aquí: son de la vacante. Al convocar de nuevo,
    los campos del post que vengan en `None` se copian de la convocatoria anterior,
    que es lo que pidió el dueño: «con los mismos datos que ya se crearon».
    """

    fecha_limite: datetime
    estado: str = "borrador"

    asunto: str | None = Field(default=None, max_length=200)
    post_cuerpo: str | None = None
    post_imagen_url: str | None = Field(default=None, max_length=500)
    post_programado_para: datetime | None = None

    @field_validator("estado")
    @classmethod
    def estado_conocido(cls, v: str) -> str:
        if v not in ESTADOS:
            raise ValueError(f"Estado inválido: {v}. Debe ser uno de {', '.join(ESTADOS)}")
        return v

    @model_validator(mode="after")
    def coherencia(self):
        if self.post_programado_para and self.post_programado_para <= datetime.now(self.post_programado_para.tzinfo):
            raise ValueError("La fecha de publicación programada ya pasó")
        return self


class ConvocatoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vacante_id: UUID
    numero: int
    fecha_limite: datetime
    estado: str
    slug: str

    asunto: str | None
    post_cuerpo: str | None
    post_imagen_url: str | None
    post_programado_para: datetime | None
    post_estado: str
    post_publicado_en: datetime | None
    post_error: str | None
    linkedin_post_id: str | None
    enviado_internamente_en: datetime | None

    url_publica: str | None = None
    # Cuántas personas se han postulado a esta convocatoria.
    postulantes: int = 0
    creado_en: datetime


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
    """Cómo se verá el post antes de publicarlo, y por dónde puede salir.

    Los tres campos de `tarjeta_*` son lo que se le manda a la red social para que
    dibuje la tarjeta del enlace. Van aquí para que la simulación enseñe **lo que de
    verdad se envía** y no una reconstrucción parecida hecha en la pantalla.
    """

    asunto: str
    cuerpo: str
    imagen_url: str | None
    enlace_para_postular: str
    visibilidad: str
    destinatarios_internos: list[str]
    programado_para: datetime | None
    caracteres: int

    tarjeta_titulo: str
    tarjeta_descripcion: str
    tarjeta_dominio: str
    # Quién aparecería publicando. Es el muro de quien conecta su cuenta.
    autor: str


class ResultadoDePublicacion(BaseModel):
    post_estado: str
    linkedin_post_id: str | None = None
    simulado: bool = False
    mensaje: str


class EnvioInternoOut(BaseModel):
    enviados: int
    mensaje: str


class WhatsAppShareOut(BaseModel):
    whatsapp_url: str


class ParaCompartirEnLinkedIn(BaseModel):
    """Lo que la pantalla necesita para llevar la convocatoria a LinkedIn a mano."""

    texto: str
    # La URL con las etiquetas Open Graph, que es la que entiende el rastreador.
    enlace_de_la_vacante: str
    url_del_compositor: str
    aviso: str
