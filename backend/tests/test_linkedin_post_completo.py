"""Lo que se le manda a LinkedIn al publicar, y qué se puede hacer después.

El punto de partida es una frase de la documentación de LinkedIn: la Posts API **no
lee la URL** para componer la tarjeta del enlace. Mandando solo el enlace —que es lo
que se hacía— la tarjeta sale sin puesto, sin descripción y sin imagen. Estas pruebas
fijan que el título, la descripción y la miniatura viajan de verdad.
"""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.core.database import SessionLocal
from app.models.vacante import TokenLinkedIn
from app.services import configuracion_service, linkedin_service

UN_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def cuenta_conectada(client, reclutador_headers):
    """Deja un token de LinkedIn guardado, como si se hubiera pegado uno del portal."""
    from app.models.usuario import Usuario

    with SessionLocal() as sesion:
        usuario = sesion.query(Usuario).filter(Usuario.email == "reclutador@atsdemo.com").one()
        token = sesion.get(TokenLinkedIn, usuario.id) or TokenLinkedIn(usuario_id=usuario.id)
        token.access_token_cifrado = configuracion_service.cifrador().encrypt(b"token-de-prueba").decode()
        token.persona_urn = "urn:li:person:ABC123"
        token.nombre_en_linkedin = "Quien Publica"
        token.expira_en = datetime.now(timezone.utc) + timedelta(days=30)
        token.revocado = False
        sesion.add(token)
        sesion.commit()
    yield
    with SessionLocal() as sesion:
        sesion.query(TokenLinkedIn).delete()
        sesion.commit()


@pytest.fixture
def imagen_en_disco(tmp_path, monkeypatch):
    """Una imagen de verdad en el volumen, porque la subida lee los bytes del archivo."""
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "media_root", str(tmp_path))
    carpeta = tmp_path / "posts"
    carpeta.mkdir()
    (carpeta / "x.png").write_bytes(UN_PNG)
    return "/api/v1/media/posts/x.png"


@pytest.fixture
def espiar_publicacion(monkeypatch):
    """Guarda con qué se llamó a LinkedIn, sin salir a internet."""
    llamadas: dict = {}

    def falso_publicar(**kwargs):
        llamadas.update(kwargs)
        return "urn:li:share:7777"

    monkeypatch.setattr(linkedin_service, "publicar_en_el_muro", falso_publicar)
    monkeypatch.setattr(linkedin_service, "subir_imagen", lambda **_: "urn:li:image:XYZ")
    return llamadas


def _publicar(client, headers, vacante):
    return client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=headers)


# -------------------------------------------------- La tarjeta del enlace


def test_se_manda_titulo_y_descripcion_de_la_tarjeta(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, cuenta_conectada, espiar_publicacion
):
    """Sin esto la tarjeta sale desnuda: LinkedIn no lee la URL para rellenarla."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta", asunto="Buscamos analista")

    _publicar(client, reclutador_headers, vacante)

    assert espiar_publicacion["titulo"] == "Buscamos analista"
    assert espiar_publicacion["descripcion"]


def test_la_imagen_del_post_llega_como_miniatura(
    client,
    reclutador_headers,
    unique_suffix,
    crear_cargo,
    crear_vacante,
    cuenta_conectada,
    espiar_publicacion,
    imagen_en_disco,
):
    """Antes la imagen se guardaba y nunca salía: el post iba solo con texto."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta", post_imagen_url=imagen_en_disco)

    _publicar(client, reclutador_headers, vacante)

    assert espiar_publicacion["imagen_urn"] == "urn:li:image:XYZ"


def test_sin_imagen_no_se_inventa_ninguna(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, cuenta_conectada, espiar_publicacion
):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")

    _publicar(client, reclutador_headers, vacante)

    assert espiar_publicacion["imagen_urn"] is None


def test_una_imagen_webp_no_tumba_la_publicacion(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, cuenta_conectada, espiar_publicacion
):
    """Nuestra subida acepta WebP y LinkedIn no.

    Publicar sin foto se ve peor; no publicar por la foto es peor todavía. Así que
    sale sin miniatura y el aviso lo dice.
    """
    vacante = crear_vacante(
        crear_cargo(unique_suffix)["id"], estado="abierta", post_imagen_url="/api/v1/media/posts/x.webp"
    )

    respuesta = _publicar(client, reclutador_headers, vacante)

    assert respuesta.status_code == 200
    assert espiar_publicacion["imagen_urn"] is None
    assert "WebP" in respuesta.json()["mensaje"] or "webp" in respuesta.json()["mensaje"]


def test_si_linkedin_rechaza_la_imagen_el_post_igual_sale(
    client,
    reclutador_headers,
    unique_suffix,
    crear_cargo,
    crear_vacante,
    cuenta_conectada,
    espiar_publicacion,
    imagen_en_disco,
    monkeypatch,
):
    def explota(**_):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(linkedin_service, "subir_imagen", explota)
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta", post_imagen_url=imagen_en_disco)

    respuesta = _publicar(client, reclutador_headers, vacante)

    assert respuesta.status_code == 200
    assert "no se envió" in respuesta.json()["mensaje"]


# ------------------------------------------------------------ El texto


def test_el_texto_lleva_la_fecha_limite_y_etiquetas(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, cuenta_conectada, espiar_publicacion
):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")

    _publicar(client, reclutador_headers, vacante)

    assert "Postulaciones hasta el" in espiar_publicacion["texto"]
    assert "#Empleo" in espiar_publicacion["texto"]


def test_las_etiquetas_van_sin_tildes():
    """Una etiqueta con tilde y otra sin ella son dos etiquetas distintas."""
    from app.api.v1.vacantes import _etiqueta

    assert _etiqueta("Analista de Reclutamiento") == "#AnalistaDeReclutamiento"
    assert _etiqueta("Administración") == "#Administracion"


# ------------------------------------------- Cambiar y borrar el post


def test_se_puede_reescribir_el_texto_del_post(
    client,
    reclutador_headers,
    unique_suffix,
    crear_cargo,
    crear_vacante,
    cuenta_conectada,
    espiar_publicacion,
    monkeypatch,
):
    cambios: dict = {}
    monkeypatch.setattr(linkedin_service, "actualizar_texto", lambda **kw: cambios.update(kw))
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    _publicar(client, reclutador_headers, vacante)

    respuesta = client.patch(f"/api/v1/vacantes/{vacante['id']}/linkedin-post", headers=reclutador_headers)

    assert respuesta.status_code == 200
    assert cambios["post_urn"] == "urn:li:share:7777"
    assert "Postula aquí" in cambios["texto"]


def test_al_borrar_el_post_la_vacante_vuelve_a_borrador(
    client,
    reclutador_headers,
    unique_suffix,
    crear_cargo,
    crear_vacante,
    cuenta_conectada,
    espiar_publicacion,
    monkeypatch,
):
    """Dejarla como publicada sería decir que hay algo en LinkedIn que ya no está."""
    monkeypatch.setattr(linkedin_service, "borrar_post", lambda **_: None)
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    _publicar(client, reclutador_headers, vacante)

    respuesta = client.delete(f"/api/v1/vacantes/{vacante['id']}/linkedin-post", headers=reclutador_headers)

    assert respuesta.status_code == 200
    actualizada = next(
        v for v in client.get("/api/v1/vacantes", headers=reclutador_headers).json() if v["id"] == vacante["id"]
    )
    assert actualizada["post_estado"] == "borrador"
    assert actualizada["linkedin_post_id"] is None


def test_no_se_toca_en_linkedin_una_publicacion_simulada(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    """Sin cuenta conectada la publicación se simula: ese id no existe en LinkedIn."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    _publicar(client, reclutador_headers, vacante)

    respuesta = client.delete(f"/api/v1/vacantes/{vacante['id']}/linkedin-post", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "simulada" in respuesta.json()["detail"]


def test_una_vacante_sin_post_no_se_puede_borrar_de_linkedin(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")

    respuesta = client.delete(f"/api/v1/vacantes/{vacante['id']}/linkedin-post", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "no está publicada" in respuesta.json()["detail"]
