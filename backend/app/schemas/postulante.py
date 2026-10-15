from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.schemas.cv_extraido import (
    EducacionExtraida,
    ExperienciaExtraida,
    IdiomaExtraido,
    RedSocial,
)


class FormacionSecundaria(BaseModel):
    institucion: str | None = None
    titulo: str | None = None
    anio: int | None = None


class FormacionSuperior(BaseModel):
    institucion: str | None = None
    titulo: str | None = None
    estado: str | None = None


class ExperienciaLaboral(BaseModel):
    cargo: str | None = None
    empresa: str | None = None
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    actualmente: bool = False


class CvParseadoOut(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    edad: int | None = None
    cedula: str | None = None
    email: str | None = None
    telefono: str | None = None
    formacion_secundaria: FormacionSecundaria | None = None
    formacion_superior: FormacionSuperior | None = None
    nivel_instruccion: str | None = None
    titulos: list[str] = []
    experiencia_laboral: list[ExperienciaLaboral] = []
    texto_extraido_parcial: str | None = None


class PostularRequest(BaseModel):
    """Lo que manda el formulario de postulación.

    Sigue el esquema de `docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx`.
    Solo son obligatorios los cuatro datos sin los que no se puede contactar ni
    identificar a nadie; el resto admite vacío, porque un CV no siempre los trae y
    no se le va a cerrar la puerta a un candidato por una casilla.
    """

    # --- Obligatorios ---
    nombres: str
    apellidos: str
    cedula: str
    email: EmailStr

    # --- Identidad ---
    tipo_documento: str | None = None
    fecha_nacimiento: date | None = None
    genero: str | None = None
    nacionalidad: str | None = None
    foto_url: str | None = None

    # --- Contacto ---
    telefono_codigo_pais: str | None = None
    telefono: str | None = None
    telefono_tipo: str | None = None
    pais_residencia: str | None = None
    provincia: str | None = None
    localidad: str | None = None

    # --- Perfil ---
    nivel_instruccion: str | None = None
    estudios_secundarios_completos: bool | None = None
    linkedin_url: str | None = None
    otras_redes: list[RedSocial] = []
    expectativas: str | None = None
    cv_documento_url: str | None = None
    edad: int | None = None

    educacion: list[EducacionExtraida] = []
    idiomas: list[IdiomaExtraido] = []
    experiencia: list[ExperienciaExtraida] = []

    respuestas_filtro: dict[str, str] = {}
    origen: str = "Directo"
    # 'manual' o 'cv': queda guardado para saber si una ficha la revisó alguien o la
    # rellenó la lectura automática sin que nadie la mirara.
    origen_datos: str = "manual"

    # Sin valor por defecto a propósito: **Pydantic no valida los valores por
    # defecto**, así que con `= False` el validador de abajo no llegaba a correr y una
    # postulación sin aceptar la política entraba igual. Al no tener defecto, quien no
    # mande el campo recibe un 422.
    acepta_privacidad: bool

    @field_validator("acepta_privacidad")
    @classmethod
    def hay_que_aceptar(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Hay que aceptar la política de privacidad para postular")
        return v


class EducacionOut(EducacionExtraida):
    model_config = ConfigDict(from_attributes=True)


class IdiomaOut(IdiomaExtraido):
    model_config = ConfigDict(from_attributes=True)


class ExperienciaOut(ExperienciaExtraida):
    model_config = ConfigDict(from_attributes=True)


class PostulanteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombres: str
    apellidos: str
    tipo_documento: str | None = None
    cedula: str
    fecha_nacimiento: date | None = None
    genero: str | None = None
    nacionalidad: str | None = None
    foto_url: str | None = None

    email: str
    telefono_codigo_pais: str | None = None
    telefono: str | None
    telefono_tipo: str | None = None
    pais_residencia: str | None = None
    provincia: str | None = None
    localidad: str | None = None

    nivel_instruccion: str | None
    estudios_secundarios_completos: bool | None = None
    linkedin_url: str | None = None
    otras_redes: list = []
    expectativas: str | None = None
    cv_documento_url: str | None = None
    origen_datos: str = "manual"
    edad: int | None

    educacion: list[EducacionOut] = []
    idiomas: list[IdiomaOut] = []
    experiencia: list[ExperienciaOut] = []

    creado_en: datetime


class ContactoOut(PostulanteOut):
    ultimo_estado_pipeline: str | None = None
    ultima_vacante: str | None = None
    total_postulaciones: int = 0
