"""Configuración de la aplicación.

`secret_key` **no tiene valor por defecto a propósito**. Firma los JWT: con un valor
conocido cualquiera puede fabricarse un token de super admin sin contraseña. Antes vivía
aquí un valor fijo que está publicado en el repositorio. Ahora, si falta, la aplicación
no arranca; es preferible un contenedor que no levanta a uno que levanta inseguro.

Para generar uno:

    python -c "import secrets; print(secrets.token_urlsafe(48))"
"""

import base64
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valores que circularon como ejemplo y están publicados: aceptarlos sería dejar la
# puerta abierta creyendo que se cerró.
SECRETOS_QUEMADOS = {
    "supersecretkey_ats_2026",
    "changeme",
    "secret",
    "mock_secret",
}

LARGO_MINIMO_DE_SECRETO = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ats_user:ats_password@db:5432/ats_db"
    secret_key: str = Field(min_length=1)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    frontend_origin: str = "http://localhost:3000"

    # Dónde se guardan las imágenes de los posts. Es un volumen montado en el
    # contenedor, así que sobrevive a `docker compose down` (no a `down -v`).
    media_root: str = "/app/media"
    media_url_base: str = "/api/v1/media"

    default_admin_email: str = "admin@atsdemo.com"
    default_admin_password: str = "Admin123!"

    @field_validator("secret_key")
    @classmethod
    def secreto_utilizable(cls, v: str) -> str:
        if v in SECRETOS_QUEMADOS:
            raise ValueError(
                f"SECRET_KEY tiene un valor de ejemplo publicado ({v!r}). Genera uno propio: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if len(v) < LARGO_MINIMO_DE_SECRETO:
            raise ValueError(f"SECRET_KEY debe tener al menos {LARGO_MINIMO_DE_SECRETO} caracteres; tiene {len(v)}")
        return v

    def clave_de_cifrado(self) -> bytes:
        """Clave Fernet para los secretos guardados en la base (LinkedIn, Gmail).

        Se deriva de `secret_key` en vez de ser otra variable más que configurar y
        rotar. La consecuencia es explícita: **al rotar SECRET_KEY, los secretos
        guardados dejan de poder descifrarse y hay que volver a introducirlos.**
        """
        derivada = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"ats:configuracion:v1",
        ).derive(self.secret_key.encode())
        return base64.urlsafe_b64encode(derivada)


@lru_cache
def get_settings() -> Settings:
    return Settings()
