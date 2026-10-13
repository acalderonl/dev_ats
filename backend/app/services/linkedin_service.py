"""Publicación en LinkedIn por la única vía que no exige ser partner aprobado.

Qué se puede y qué no, comprobado en octubre de 2026:

| Destino                         | Cómo se consigue                                      |
|---------------------------------|-------------------------------------------------------|
| Muro del propio usuario         | Autoservicio: productos *Sign In with LinkedIn (OIDC)* |
|                                 | y *Share on LinkedIn* -> scope `w_member_social`.      |
| Página de empresa               | Community Management API: aprobación de partner.       |
| Tablón de empleos de LinkedIn   | Talent Solutions (RSC / Apply Connect): partner.       |

La versión anterior de este archivo llamaba a `/v2/jobPostings`, que es justo la vía
cerrada: nunca habría funcionado con credenciales normales. Esto publica en el muro
del reclutador que conecta su cuenta, que es lo que sí está a nuestro alcance.

Dos límites de la vía de autoservicio que el código asume:

- **El token dura ~60 días y no hay refresh token** para quien no es partner. Por eso
  se guarda `expira_en` y hay que volver a conectar. No se intenta renovar.
- `ugcPosts` es la API vieja. Se usa `/rest/posts`, que exige las cabeceras
  `LinkedIn-Version` y `X-Restli-Protocol-Version` en cada llamada.

Sin credenciales configuradas, el servicio queda en **modo simulado**: devuelve un id
determinístico sin salir a internet, para poder recorrer el flujo entero.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.services import configuracion_service

AUTORIZACION = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO = "https://api.linkedin.com/v2/userinfo"
POSTS = "https://api.linkedin.com/rest/posts"
IMAGENES = "https://api.linkedin.com/rest/images"

# LinkedIn versiona por mes. Subirla es un cambio consciente, no automático.
VERSION_API = "202410"
SCOPES = "openid profile w_member_social"

CABECERAS_BASE = {
    "LinkedIn-Version": VERSION_API,
    "X-Restli-Protocol-Version": "2.0.0",
}


class LinkedInNoConfigurado(RuntimeError):
    """Faltan client id/secret: no se puede ni empezar el flujo OAuth."""


class LinkedInSinConexion(RuntimeError):
    """El usuario no ha conectado su cuenta, o su token caducó."""


def credenciales(db: Session) -> tuple[str, str, str] | None:
    """(client_id, client_secret, redirect_uri) o None si falta algo."""
    client_id = configuracion_service.leer(db, "linkedin_client_id")
    client_secret = configuracion_service.leer_secreto(db, "linkedin_client_secret")
    redirect_uri = configuracion_service.leer(db, "linkedin_redirect_uri")
    if not (client_id and client_secret and redirect_uri):
        return None
    return client_id, client_secret, redirect_uri


def esta_configurado(db: Session) -> bool:
    return credenciales(db) is not None


# --------------------------------------------------------------------------- OAuth


def url_de_autorizacion(db: Session) -> tuple[str, str]:
    """Devuelve (url a la que mandar al usuario, state que hay que guardar).

    El `state` es aleatorio y se compara al volver: sin eso, un tercero podría
    enganchar su propia cuenta de LinkedIn a la sesión de otro.
    """
    datos = credenciales(db)
    if datos is None:
        raise LinkedInNoConfigurado("Falta configurar client id, secret y redirect uri de LinkedIn")
    client_id, _, redirect_uri = datos
    state = secrets.token_urlsafe(24)
    url = (
        f"{AUTORIZACION}?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={httpx.URL(redirect_uri)}"
        f"&state={state}"
        f"&scope={SCOPES.replace(' ', '%20')}"
    )
    return url, state


def canjear_codigo(db: Session, codigo: str) -> dict:
    """Cambia el código de un solo uso por un token, y pregunta de quién es.

    Devuelve {access_token, expira_en, persona_urn, nombre}.
    """
    datos = credenciales(db)
    if datos is None:
        raise LinkedInNoConfigurado("Falta configurar las credenciales de LinkedIn")
    client_id, client_secret, redirect_uri = datos

    with httpx.Client(timeout=20) as cliente:
        respuesta = cliente.post(
            TOKEN,
            data={
                "grant_type": "authorization_code",
                "code": codigo,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        respuesta.raise_for_status()
        token = respuesta.json()

        perfil = cliente.get(USERINFO, headers={"Authorization": f"Bearer {token['access_token']}"})
        perfil.raise_for_status()
        datos_perfil = perfil.json()

    segundos = int(token.get("expires_in", 60 * 60 * 24 * 60))
    return {
        "access_token": token["access_token"],
        "expira_en": datetime.now(timezone.utc) + timedelta(seconds=segundos),
        "persona_urn": f"urn:li:person:{datos_perfil['sub']}",
        "nombre": datos_perfil.get("name"),
    }


# ------------------------------------------------------------------------ Publicar


def _publicar_simulado(vacante_id: uuid.UUID, titulo: str) -> str:
    digest = hashlib.sha1(f"{vacante_id}:{titulo}".encode()).hexdigest()[:12]
    return f"urn:li:share:simulado-{digest}"


def publicar_en_el_muro(
    *,
    access_token: str,
    persona_urn: str,
    texto: str,
    enlace: str | None = None,
    imagen_urn: str | None = None,
) -> str:
    """Publica y devuelve el URN del post."""
    contenido: dict = {}
    if imagen_urn:
        contenido = {"media": {"id": imagen_urn}}
    elif enlace:
        contenido = {"article": {"source": enlace}}

    cuerpo = {
        "author": persona_urn,
        "commentary": texto,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED",
    }
    if contenido:
        cuerpo["content"] = contenido

    with httpx.Client(timeout=30) as cliente:
        respuesta = cliente.post(
            POSTS,
            json=cuerpo,
            headers={**CABECERAS_BASE, "Authorization": f"Bearer {access_token}"},
        )
        respuesta.raise_for_status()
        # El id viene en la cabecera, no en el cuerpo (el cuerpo suele venir vacío).
        return respuesta.headers.get("x-restli-id") or respuesta.json().get("id", "")
