"""La forma de lo que se saca de un CV.

Este archivo es a la vez el esquema de salida que se le **impone al modelo** (se pasa
a `messages.parse`, que valida la respuesta contra él) y el contrato que consume el
formulario. Que sea uno solo evita que se desincronicen.

**Todo es opcional a propósito.** Un CV no trae la provincia, ni el tipo de documento,
ni la subárea de trabajo. Obligar esos campos empujaría al modelo a rellenarlos con
algo, y un dato inventado en una ficha de candidato es peor que una casilla vacía:
nadie vuelve a revisarlo.
"""

from pydantic import BaseModel, Field

MES_MINIMO = 1
MES_MAXIMO = 12
ANIO_MINIMO = 1940
ANIO_MAXIMO = 2100


class EducacionExtraida(BaseModel):
    titulo: str | None = Field(default=None, description="Título obtenido o en curso, tal como aparece")
    pais: str | None = None
    institucion: str | None = Field(default=None, description="Universidad, instituto o colegio")
    area_estudio: str | None = Field(default=None, description="Campo de estudio, p. ej. Psicología")
    nivel_estudio: str | None = Field(
        default=None, description="Secundaria, Técnico, Universitario, Máster, Posgrado, Doctorado"
    )
    estado_estudio: str | None = Field(default=None, description="Graduado, En curso o Incompleto")
    inicio_mes: int | None = Field(default=None, ge=MES_MINIMO, le=MES_MAXIMO)
    inicio_anio: int | None = Field(default=None, ge=ANIO_MINIMO, le=ANIO_MAXIMO)
    actualmente: bool = Field(default=False, description="True si sigue estudiando ahí")
    fin_mes: int | None = Field(default=None, ge=MES_MINIMO, le=MES_MAXIMO)
    fin_anio: int | None = Field(default=None, ge=ANIO_MINIMO, le=ANIO_MAXIMO)
    descripcion: str | None = None


class IdiomaExtraido(BaseModel):
    idioma: str
    nivel_escrito: str | None = Field(default=None, description="Básico, Intermedio, Avanzado o Nativo")
    nivel_oral: str | None = Field(default=None, description="Básico, Intermedio, Avanzado o Nativo")


class ExperienciaExtraida(BaseModel):
    puesto: str | None = Field(default=None, description="Cargo desempeñado")
    jerarquia: str | None = Field(
        default=None, description="Junior, Semi-Senior, Senior, Jefatura o Dirección, si se deduce del puesto"
    )
    empresa: str | None = None
    pais: str | None = None
    industria: str | None = Field(default=None, description="Sector de la empresa, p. ej. Educación")
    area_trabajo: str | None = Field(default=None, description="Área funcional, p. ej. Recursos Humanos")
    subarea_trabajo: str | None = None
    inicio_mes: int | None = Field(default=None, ge=MES_MINIMO, le=MES_MAXIMO)
    inicio_anio: int | None = Field(default=None, ge=ANIO_MINIMO, le=ANIO_MAXIMO)
    actualmente: bool = Field(default=False, description="True si es su trabajo actual")
    fin_mes: int | None = Field(default=None, ge=MES_MINIMO, le=MES_MAXIMO)
    fin_anio: int | None = Field(default=None, ge=ANIO_MINIMO, le=ANIO_MAXIMO)
    descripcion: str | None = Field(default=None, description="Funciones y logros, resumidos del CV")


class RedSocial(BaseModel):
    red: str
    url: str


class CvExtraido(BaseModel):
    """Todo lo que se pudo leer del CV. Lo que no estaba, va en `None`."""

    nombres: str | None = None
    apellidos: str | None = None
    email: str | None = None
    tipo_documento: str | None = Field(default=None, description="Cédula, Pasaporte o similar")
    numero_documento: str | None = Field(default=None, description="Número de cédula o pasaporte")
    fecha_nacimiento: str | None = Field(default=None, description="AAAA-MM-DD si consta completa")

    telefono_codigo_pais: str | None = Field(default=None, description="Con el +, p. ej. +593")
    telefono: str | None = Field(default=None, description="Solo el número, sin el código de país")
    telefono_tipo: str | None = Field(default=None, description="Celular/Móvil, Fijo o Trabajo")

    genero: str | None = None
    nacionalidad: str | None = None
    pais_residencia: str | None = None
    provincia: str | None = None
    localidad: str | None = Field(default=None, description="Ciudad de residencia")

    estudios_secundarios_completos: bool | None = None
    linkedin_url: str | None = None
    otras_redes: list[RedSocial] = []

    educacion: list[EducacionExtraida] = []
    idiomas: list[IdiomaExtraido] = []
    experiencia: list[ExperienciaExtraida] = []


class CvExtraidoOut(CvExtraido):
    """Lo mismo, más cómo fue la extracción. La pantalla necesita ambas cosas."""

    # 'claude', 'heuristicas' o 'vacio': quien usa esto debe poder distinguir entre
    # "el CV no lo decía" y "no había extractor configurado".
    motor: str
    aviso: str | None = None
    campos_encontrados: int = 0
    # Dónde quedó guardado el archivo subido. Hasta ahora el CV se leía y se tiraba:
    # quedaba lo que la extracción hubiera entendido y nada con qué contrastarlo.
    cv_documento_url: str | None = None
