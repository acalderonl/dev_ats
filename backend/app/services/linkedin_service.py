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
from urllib.parse import quote

import httpx
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
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


MINUTOS_DE_VIDA_DEL_STATE = 10


class StateInvalido(RuntimeError):
    """El `state` que volvió de LinkedIn no es el que se mandó."""


def _firmar_state(usuario_id: uuid.UUID) -> str:
    """El `state` va firmado en vez de guardado en una tabla.

    Lleva dentro a quién pertenece y cuándo caduca, así que al volver se comprueba
    sin consultar nada y no quedan filas pendientes de limpiar. Sin esta
    comprobación, un tercero podría enganchar **su** cuenta de LinkedIn a la sesión
    de otra persona mandándole un enlace de vuelta preparado.
    """
    ahora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario_id),
        "typ": "linkedin_oauth",
        "nonce": secrets.token_urlsafe(8),
        "exp": ahora + timedelta(minutes=MINUTOS_DE_VIDA_DEL_STATE),
    }
    ajustes = get_settings()
    return jwt.encode(carga, ajustes.secret_key, algorithm=ajustes.algorithm)


def verificar_state(state: str, usuario_id: uuid.UUID) -> None:
    """Lanza `StateInvalido` si el state no es de este usuario o ya caducó."""
    ajustes = get_settings()
    try:
        carga = jwt.decode(state, ajustes.secret_key, algorithms=[ajustes.algorithm])
    except JWTError:
        raise StateInvalido("La conexión con LinkedIn caducó o no es válida. Vuelve a empezar.")
    if carga.get("typ") != "linkedin_oauth" or carga.get("sub") != str(usuario_id):
        raise StateInvalido("Esta conexión con LinkedIn se inició desde otra sesión.")


def url_de_autorizacion(db: Session, usuario_id: uuid.UUID) -> tuple[str, str]:
    """Devuelve (url a la que mandar al usuario, state firmado)."""
    datos = credenciales(db)
    if datos is None:
        raise LinkedInNoConfigurado("Falta configurar client id, secret y redirect uri de LinkedIn")
    client_id, _, redirect_uri = datos
    state = _firmar_state(usuario_id)
    url = (
        f"{AUTORIZACION}?response_type=code"
        f"&client_id={quote(client_id, safe='')}"
        f"&redirect_uri={quote(redirect_uri, safe='')}"
        f"&state={quote(state, safe='')}"
        f"&scope={quote(SCOPES, safe='')}"
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


# Lo que dura un token del generador de LinkedIn. No viene escrito en el token y
# LinkedIn no lo dice al preguntar por el perfil: su propia pantalla anuncia ~2
# meses. Solo sirve para avisar antes de tiempo; si se queda corto o largo, quien
# manda es LinkedIn devolviendo 401 al publicar.
DIAS_DEL_TOKEN_PEGADO = 60


class TokenRechazado(RuntimeError):
    """LinkedIn no aceptó el token pegado, o le falta permiso para publicar."""


def identificar(access_token: str) -> dict:
    """Pregunta a LinkedIn de quién es un token ya emitido.

    Es el atajo del *Token generator* del portal de desarrolladores: evita montar el
    ida y vuelta de OAuth —y con él la Redirect URI, que es donde más se rompe— a
    cambio de volver a pegar un token cada ~60 días.

    Devuelve {access_token, expira_en, persona_urn, nombre}, lo mismo que
    `canjear_codigo`, para que a partir de aquí los dos caminos sean el mismo.
    """
    with httpx.Client(timeout=20) as cliente:
        perfil = cliente.get(USERINFO, headers={"Authorization": f"Bearer {access_token}"})

    if perfil.status_code in (401, 403):
        raise TokenRechazado(
            "LinkedIn no acepta ese token: puede estar mal copiado, caducado, "
            "o generado sin los permisos 'openid' y 'profile'."
        )
    perfil.raise_for_status()
    datos = perfil.json()

    if "sub" not in datos:
        raise TokenRechazado("LinkedIn no dice de quién es el token; genéralo con el permiso 'openid'.")

    return {
        "access_token": access_token,
        "expira_en": datetime.now(timezone.utc) + timedelta(days=DIAS_DEL_TOKEN_PEGADO),
        "persona_urn": f"urn:li:person:{datos['sub']}",
        "nombre": datos.get("name"),
    }


# ------------------------------------------------------------------------ Publicar


def _publicar_simulado(vacante_id: uuid.UUID, titulo: str) -> str:
    digest = hashlib.sha1(f"{vacante_id}:{titulo}".encode()).hexdigest()[:12]
    return f"urn:li:share:simulado-{digest}"


# Lo que acepta la API de imágenes de LinkedIn. **WebP no está**, aunque nuestra
# subida sí lo admita para la imagen del post: en ese caso se publica sin miniatura y
# se dice, en vez de tumbar la publicación entera por la foto.
FORMATOS_DE_IMAGEN_EN_LINKEDIN = {".jpg", ".jpeg", ".png", ".gif"}

# Topes de la tarjeta. Más largo lo corta LinkedIn por su cuenta; cortarlo aquí deja
# el corte donde se decidió y no a mitad de palabra.
LARGO_DEL_TITULO = 200
LARGO_DE_LA_DESCRIPCION = 300


def subir_imagen(*, access_token: str, persona_urn: str, contenido: bytes, nombre: str) -> str:
    """Sube una imagen y devuelve su URN, para usarla en un post.

    Son dos pasos porque LinkedIn no acepta el archivo en la misma llamada: primero se
    registra la subida y devuelve una URL, y luego se manda el archivo a esa URL.
    """
    with httpx.Client(timeout=60) as cliente:
        registro = cliente.post(
            f"{IMAGENES}?action=initializeUpload",
            json={"initializeUploadRequest": {"owner": persona_urn}},
            headers={**CABECERAS_BASE, "Authorization": f"Bearer {access_token}"},
        )
        registro.raise_for_status()
        valor = registro.json()["value"]

        subida = cliente.put(
            valor["uploadUrl"],
            content=contenido,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        subida.raise_for_status()

    _ = nombre  # El nombre no viaja: LinkedIn identifica la imagen por su URN.
    return valor["image"]


def publicar_en_el_muro(
    *,
    access_token: str,
    persona_urn: str,
    texto: str,
    enlace: str | None = None,
    titulo: str | None = None,
    descripcion: str | None = None,
    imagen_urn: str | None = None,
) -> str:
    """Publica y devuelve el URN del post.

    El título, la descripción y la miniatura **hay que mandarlos**: la documentación
    de LinkedIn dice que la Posts API *no* lee la URL para componer la tarjeta («does
    not support URL scraping for article post creation»). Mandando solo el enlace, la
    tarjeta sale desnuda. Las etiquetas Open Graph de `/compartir` siguen haciendo
    falta, pero para el otro camino: el del compositor, donde LinkedIn sí las lee.
    """
    cuerpo: dict = {
        "author": persona_urn,
        "commentary": texto,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED",
    }

    if enlace:
        articulo: dict = {"source": enlace}
        if titulo:
            articulo["title"] = titulo[:LARGO_DEL_TITULO]
        if descripcion:
            articulo["description"] = descripcion[:LARGO_DE_LA_DESCRIPCION]
        if imagen_urn:
            articulo["thumbnail"] = imagen_urn
        cuerpo["content"] = {"article": articulo}
    elif imagen_urn:
        # Sin enlace que enmarcar, la imagen es el contenido del post.
        cuerpo["content"] = {"media": {"id": imagen_urn, "altText": titulo or ""}}

    with httpx.Client(timeout=30) as cliente:
        respuesta = cliente.post(
            POSTS,
            json=cuerpo,
            headers={**CABECERAS_BASE, "Authorization": f"Bearer {access_token}"},
        )
        respuesta.raise_for_status()
        # El id viene en la cabecera, no en el cuerpo (el cuerpo suele venir vacío).
        return respuesta.headers.get("x-restli-id") or respuesta.json().get("id", "")


def actualizar_texto(*, access_token: str, post_urn: str, texto: str) -> None:
    """Cambia el texto de un post ya publicado.

    Es lo único que la API deja reescribir del contenido: ni el enlace ni la imagen.
    Sirve para arreglar una errata o para volver a sincronizar el post con la vacante
    después de editarla.
    """
    with httpx.Client(timeout=30) as cliente:
        respuesta = cliente.post(
            f"{POSTS}/{quote(post_urn, safe='')}",
            json={"patch": {"$set": {"commentary": texto}}},
            headers={
                **CABECERAS_BASE,
                "Authorization": f"Bearer {access_token}",
                "X-RestLi-Method": "PARTIAL_UPDATE",
            },
        )
        respuesta.raise_for_status()


def borrar_post(*, access_token: str, post_urn: str) -> None:
    """Borra el post de LinkedIn.

    LinkedIn responde 204 también si ya no existía, así que llamar dos veces no es un
    error: deja de existir, que es lo que se pedía.
    """
    with httpx.Client(timeout=30) as cliente:
        respuesta = cliente.delete(
            f"{POSTS}/{quote(post_urn, safe='')}",
            headers={
                **CABECERAS_BASE,
                "Authorization": f"Bearer {access_token}",
                "X-RestLi-Method": "DELETE",
            },
        )
        respuesta.raise_for_status()
