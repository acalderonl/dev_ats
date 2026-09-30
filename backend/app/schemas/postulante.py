from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


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
    nombres: str
    apellidos: str
    cedula: str
    email: EmailStr
    telefono: str | None = None
    edad: int | None = None
    formacion_secundaria: FormacionSecundaria | None = None
    formacion_superior: FormacionSuperior | None = None
    nivel_instruccion: str | None = None
    titulos: list[str] = []
    experiencia_laboral: list[ExperienciaLaboral] = []
    respuestas_filtro: dict[str, str] = {}
    origen: str = "Directo"


class PostulanteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombres: str
    apellidos: str
    cedula: str
    email: str
    telefono: str | None
    edad: int | None
    formacion_secundaria: dict | None
    formacion_superior: dict | None
    nivel_instruccion: str | None
    titulos: list[str] | None
    experiencia_laboral: list | None
    cv_documento_url: str
    creado_en: datetime


class ContactoOut(PostulanteOut):
    ultimo_estado_pipeline: str | None = None
    ultima_vacante: str | None = None
    total_postulaciones: int = 0
