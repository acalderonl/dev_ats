from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

TipoRespuesta = Literal["multiple", "unica", "texto", "booleano", "numero"]

# 7. Experiencia requerida. El orden de la tupla es el de la barra en pantalla.
ExperienciaRequerida = Literal["ninguna", "hasta_1", "1_a_3", "3_a_5", "mas_de_5"]

# 4. Acompaña al nivel de educación: si se exige terminado o basta con estar cursándolo.
EstadoEducacion = Literal["completa", "en_curso"]

TipoCompetencia = Literal["academico", "blanda"]


class Actividad(BaseModel):
    texto: str
    favorita: bool = False


def _ordenar_actividades(actividades: list[Actividad]) -> list[Actividad]:
    """Descarta las vacías y sube las favoritas, conservando el orden dentro de cada grupo."""
    limpias = [a for a in actividades if a.texto and a.texto.strip()]
    for actividad in limpias:
        actividad.texto = actividad.texto.strip()
    return sorted(limpias, key=lambda a: not a.favorita)


class CompetenciaDelCargo(BaseModel):
    competencia_id: int
    requerido: bool = False
    deseado: bool = False

    @model_validator(mode="after")
    def exigencia_excluyente(self) -> "CompetenciaDelCargo":
        """Una competencia es requisito o es deseable, nunca las dos a la vez."""
        if self.requerido and self.deseado:
            raise ValueError("Una competencia no puede ser requerida y deseada al mismo tiempo")
        return self


class CompetenciaDelCargoOut(CompetenciaDelCargo):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    tipo: str


class CargoCreate(BaseModel):
    nombre_id: int
    tiene_personal_a_cargo: bool = False
    clasificacion_id: int | None = None
    mision: str | None = None
    actividades: list[Actividad] = []
    nivel_educacion_id: int | None = None
    estado_educacion: EstadoEducacion | None = None
    titulo_id: int | None = None
    area_academica_id: int | None = None
    experiencia_requerida: ExperienciaRequerida | None = None
    competencias: list[CompetenciaDelCargo] = []

    @field_validator("actividades")
    @classmethod
    def limpiar_y_ordenar(cls, v: list[Actividad]) -> list[Actividad]:
        return _ordenar_actividades(v)


class CargoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_id: int
    nombre: str
    tiene_personal_a_cargo: bool
    clasificacion_id: int | None
    clasificacion: str | None
    mision: str | None
    actividades: list[Actividad]
    nivel_educacion_id: int | None
    nivel_educacion: str | None
    estado_educacion: str | None
    titulo_id: int | None
    titulo: str | None
    area_academica_id: int | None
    area_academica: str | None
    experiencia_requerida: str | None
    competencias: list[CompetenciaDelCargoOut] = []
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
