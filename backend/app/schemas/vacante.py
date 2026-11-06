from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.vacante import VISIBILIDADES
from app.schemas.cargo import PreguntaFiltroOut
from app.schemas.convocatoria import ConvocatoriaCreate, ConvocatoriaOut

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
    """Las condiciones del puesto. El título no está: sale del cargo.

    `primera_convocatoria` solo cuenta al **crear**: una vacante nace con su
    convocatoria 1, para que «Nueva vacante» siga siendo un paso y no dos. Al editar se
    ignora; el ciclo se toca desde `/convocatorias`.
    """

    cargo_id: int
    descripcion: str

    remuneracion: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    jornada_horas: Decimal | None = Field(default=None, gt=0, le=24, max_digits=4, decimal_places=2)
    hora_entrada: time | None = None
    hora_salida: time | None = None
    tipo_contrato_id: int | None = None
    campos_personalizados: list[CampoPersonalizado] = []

    visibilidad: str = "publica"
    destinatarios_internos: list[EmailStr] = []

    primera_convocatoria: ConvocatoriaCreate | None = None

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

    remuneracion: Decimal | None
    jornada_horas: Decimal | None
    hora_entrada: time | None
    hora_salida: time | None
    tipo_contrato_id: int | None
    # Nombre resuelto. Se llama distinto que la relación del modelo a propósito:
    # `model_validate` mapea por nombre y tomaría el objeto ORM en lugar del texto.
    tipo_contrato_nombre: str | None = None
    campos_personalizados: list[CampoPersonalizado]

    visibilidad: str
    destinatarios_internos: list[str]

    empleador_id: UUID
    activa: bool
    creado_en: datetime

    # De la más reciente a la primera. La actual es la primera de la lista.
    convocatorias: list[ConvocatoriaOut] = []
    convocatoria_actual: ConvocatoriaOut | None = None


class VacantePublicaOut(BaseModel):
    """Lo que ve el candidato. `id` y `slug` son de la **convocatoria**: es a lo que se postula."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vacante_id: UUID
    numero: int
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


class ImagenSubidaOut(BaseModel):
    url: str
