from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfiguracionUpdate(BaseModel):
    """Todo opcional: un campo ausente no se toca.

    Importa para los secretos. La pantalla nunca los recibe, así que los manda vacíos;
    si "vacío" significara "bórralo", abrir Configuración y guardar cualquier otra cosa
    borraría las credenciales.
    """

    empresa_nombre: str | None = None
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None
    linkedin_redirect_uri: str | None = None
    gmail_remitente: str | None = None
    gmail_password_app: str | None = None
    dominios_corporativos: str | None = None


class ConfiguracionOut(BaseModel):
    empresa_nombre: str | None = None
    linkedin_client_id: str | None = None
    linkedin_redirect_uri: str | None = None
    gmail_remitente: str | None = None
    dominios_corporativos: str | None = None

    # Los secretos se informan, no se devuelven.
    linkedin_client_secret: None = None
    linkedin_client_secret_configurado: bool = False
    linkedin_client_secret_pista: str | None = None
    gmail_password_app: None = None
    gmail_password_app_configurado: bool = False
    gmail_password_app_pista: str | None = None


class EstadoLinkedIn(BaseModel):
    credenciales_configuradas: bool
    cuenta_conectada: bool
    nombre_en_linkedin: str | None = None
    expira_en: datetime | None = None
    correo_configurado: bool = False


class UrlDeConexion(BaseModel):
    url: str
    state: str


class JornadaCreate(BaseModel):
    nombre: str = Field(max_length=100)
    horas: Decimal = Field(gt=0, le=24, max_digits=4, decimal_places=2)

    @field_validator("nombre")
    @classmethod
    def con_contenido(cls, v: str) -> str:
        limpio = v.strip()
        if not limpio:
            raise ValueError("El nombre de la jornada no puede estar vacío")
        return limpio


class JornadaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    horas: Decimal | None = Field(default=None, gt=0, le=24, max_digits=4, decimal_places=2)
    activo: bool | None = None


class JornadaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    horas: Decimal
    activo: bool
