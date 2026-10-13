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


# Tope de la sección 4: como mucho dos niveles, dos títulos y dos áreas por cargo.
MAXIMO_POR_CAMPO_DE_EDUCACION = 2


class NivelDelCargo(BaseModel):
    nivel_id: int
    estado: EstadoEducacion = "completa"


class NivelDelCargoOut(NivelDelCargo):
    model_config = ConfigDict(from_attributes=True)

    nombre: str


class ItemDeEducacionOut(BaseModel):
    """Un título o un área ya elegidos: el id para el formulario, el nombre para mostrar."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


def _validar_tope(valores: list, etiqueta: str) -> list:
    if len(valores) > MAXIMO_POR_CAMPO_DE_EDUCACION:
        raise ValueError(f"Como máximo {MAXIMO_POR_CAMPO_DE_EDUCACION} {etiqueta} por cargo")
    return valores


def _sin_repetidos(ids: list[int], etiqueta: str) -> list[int]:
    if len(set(ids)) != len(ids):
        raise ValueError(f"No se puede elegir dos veces el mismo {etiqueta}")
    return ids


class CargoCreate(BaseModel):
    nombre_id: int
    tiene_personal_a_cargo: bool = False
    clasificacion_id: int | None = None
    mision: str | None = None
    actividades: list[Actividad] = []
    niveles_educacion: list[NivelDelCargo] = []
    titulos_ids: list[int] = []
    areas_academicas_ids: list[int] = []
    experiencia_requerida: ExperienciaRequerida | None = None
    experiencia_empresas_similares: bool = False
    experiencia_cargos_similares: bool = False
    experiencia_interna_otros_cargos: bool = False
    competencias: list[CompetenciaDelCargo] = []

    @field_validator("actividades")
    @classmethod
    def limpiar_y_ordenar(cls, v: list[Actividad]) -> list[Actividad]:
        return _ordenar_actividades(v)

    @field_validator("niveles_educacion")
    @classmethod
    def tope_niveles(cls, v: list[NivelDelCargo]) -> list[NivelDelCargo]:
        _sin_repetidos([n.nivel_id for n in v], "nivel de educación")
        return _validar_tope(v, "niveles de educación")

    @field_validator("titulos_ids")
    @classmethod
    def tope_titulos(cls, v: list[int]) -> list[int]:
        _sin_repetidos(v, "título")
        return _validar_tope(v, "títulos")

    @field_validator("areas_academicas_ids")
    @classmethod
    def tope_areas(cls, v: list[int]) -> list[int]:
        _sin_repetidos(v, "área académica")
        return _validar_tope(v, "áreas académicas")


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
    niveles_educacion: list[NivelDelCargoOut] = []
    titulos: list[ItemDeEducacionOut] = []
    areas_academicas: list[ItemDeEducacionOut] = []
    experiencia_requerida: str | None
    experiencia_empresas_similares: bool
    experiencia_cargos_similares: bool
    experiencia_interna_otros_cargos: bool
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
