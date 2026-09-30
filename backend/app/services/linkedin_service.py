"""Cliente para la API de LinkedIn Job Posting.

Mientras no se configuren credenciales reales (LINKEDIN_CLIENT_ID/SECRET distintos
de los valores mock por defecto), este servicio simula la publicación y genera un
`linkedin_post_id` determinístico para permitir probar el flujo end-to-end. Cuando
se cuente con credenciales reales, reemplazar `_publish_mock` por una llamada HTTP
(httpx) al endpoint oficial de LinkedIn usando el mismo contrato de entrada/salida.
"""

import hashlib
import uuid

from app.core.config import get_settings

settings = get_settings()


def _is_mock_mode() -> bool:
    return settings.linkedin_client_id == "mock_client_id"


def _publish_mock(vacante_id: uuid.UUID, titulo: str) -> str:
    digest = hashlib.sha1(f"{vacante_id}:{titulo}".encode()).hexdigest()[:10]
    return f"li_{digest}"


def publish_job_posting(
    vacante_id: uuid.UUID,
    titulo: str,
    descripcion: str,
    ubicacion: str = "Ecuador",
    tipo_empleo: str = "FULL_TIME",
    apply_url: str | None = None,
) -> str:
    """Publica la vacante en LinkedIn y devuelve el linkedin_post_id."""
    if _is_mock_mode():
        return _publish_mock(vacante_id, titulo)

    # Integración real (requiere credenciales OAuth2 de LinkedIn Job Posting API):
    # payload = {
    #     "title": titulo,
    #     "description": descripcion,
    #     "location": ubicacion,
    #     "employmentStatus": tipo_empleo,
    #     "companyApplyUrl": apply_url,
    # }
    # response = httpx.post("https://api.linkedin.com/v2/jobPostings", json=payload, headers=...)
    # return response.json()["id"]
    raise NotImplementedError("Integración real de LinkedIn API no configurada en este entorno")
