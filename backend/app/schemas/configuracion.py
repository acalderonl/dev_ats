from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.correo_service import CIFRADOS as CIFRADOS_SMTP
from app.services.correo_service import TIPOS as TIPOS_DE_CORREO


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
    correo_tipo: str | None = None
    gmail_remitente: str | None = None
    gmail_password_app: str | None = None
    smtp_servidor: str | None = None
    smtp_puerto: str | None = None
    smtp_cifrado: str | None = None
    smtp_usuario: str | None = None
    smtp_remitente: str | None = None
    smtp_password: str | None = None
    dominios_corporativos: str | None = None
    anthropic_api_key: str | None = None
    anthropic_modelo: str | None = None

    @field_validator("correo_tipo")
    @classmethod
    def tipo_conocido(cls, v: str | None) -> str | None:
        if v and v not in TIPOS_DE_CORREO:
            raise ValueError(f"Tipo de correo inválido: {v}. Debe ser uno de {', '.join(TIPOS_DE_CORREO)}")
        return v

    @field_validator("smtp_cifrado")
    @classmethod
    def cifrado_conocido(cls, v: str | None) -> str | None:
        if v and v not in CIFRADOS_SMTP:
            raise ValueError(f"Cifrado inválido: {v}. Debe ser uno de {', '.join(CIFRADOS_SMTP)}")
        return v

    @field_validator("smtp_puerto")
    @classmethod
    def puerto_valido(cls, v: str | None) -> str | None:
        if not v:
            return v
        try:
            numero = int(v)
        except ValueError:
            raise ValueError("El puerto SMTP debe ser un número")
        if not 1 <= numero <= 65535:
            raise ValueError("El puerto SMTP debe estar entre 1 y 65535")
        return str(numero)


class ConfiguracionOut(BaseModel):
    empresa_nombre: str | None = None
    linkedin_client_id: str | None = None
    linkedin_redirect_uri: str | None = None
    correo_tipo: str | None = None
    gmail_remitente: str | None = None
    smtp_servidor: str | None = None
    smtp_puerto: str | None = None
    smtp_cifrado: str | None = None
    smtp_usuario: str | None = None
    smtp_remitente: str | None = None
    dominios_corporativos: str | None = None
    anthropic_modelo: str | None = None

    # Los secretos se informan, no se devuelven.
    linkedin_client_secret: None = None
    linkedin_client_secret_configurado: bool = False
    linkedin_client_secret_pista: str | None = None
    gmail_password_app: None = None
    gmail_password_app_configurado: bool = False
    gmail_password_app_pista: str | None = None
    smtp_password: None = None
    smtp_password_configurado: bool = False
    smtp_password_pista: str | None = None
    anthropic_api_key: None = None
    anthropic_api_key_configurado: bool = False
    anthropic_api_key_pista: str | None = None


class PruebaDeCorreo(BaseModel):
    ok: bool
    mensaje: str


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


class RetornoDeLinkedIn(BaseModel):
    """Lo que la página de retorno recoge de la URL y manda al backend."""

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
