"""La foto y el CV de un candidato: dónde se guardan y quién puede verlos.

Lo que de verdad se protege aquí: que esos archivos **no** salgan por `/media`, que va
sin autenticación porque la imagen de un post tiene que poder verla LinkedIn. Un
nombre de archivo difícil de adivinar no es un control de acceso.
"""

import pytest

from app.core.config import get_settings

# Cabeceras reales: el servidor mira los bytes, no la extensión que diga el cliente.
UN_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
UN_PDF = b"%PDF-1.4\n" + b"0" * 64
UN_DOC_ANTIGUO = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64


@pytest.fixture(autouse=True)
def media_temporal(tmp_path, monkeypatch):
    """Escribe en una carpeta de usar y tirar, no en el volumen de desarrollo."""
    monkeypatch.setattr(get_settings(), "media_root", str(tmp_path))
    yield


def _subir(client, ruta: str, nombre: str, contenido: bytes):
    return client.post(f"/api/v1/public/{ruta}", files={"file": (nombre, contenido, "application/octet-stream")})


# ------------------------------------------------------------------- Subir


def test_la_foto_se_guarda_y_devuelve_una_url_privada(client):
    respuesta = _subir(client, "foto", "yo.png", UN_PNG)

    assert respuesta.status_code == 200
    assert respuesta.json()["url"].startswith("/api/v1/archivos/postulantes/")


def test_una_foto_que_no_es_imagen_se_rechaza(client):
    """El tipo se decide por los bytes: un `.png` puede ser cualquier cosa."""
    respuesta = _subir(client, "foto", "yo.png", b"esto es texto, no una imagen")

    assert respuesta.status_code == 400


def test_el_cv_se_guarda(client):
    respuesta = _subir(client, "cv", "hoja-de-vida.pdf", UN_PDF)

    assert respuesta.status_code == 200
    assert respuesta.json()["url"].endswith(".pdf")


def test_el_doc_binario_antiguo_no_se_acepta(client):
    """El lector de CV tampoco lo soporta: aceptarlo sería prometer algo a medias."""
    respuesta = _subir(client, "cv", "hoja.doc", UN_DOC_ANTIGUO)

    assert respuesta.status_code == 400
    assert "PDF" in respuesta.json()["detail"]


def test_la_extension_la_pone_el_servidor(client):
    """El nombre que suba el cliente no se usa para construir la ruta."""
    respuesta = _subir(client, "foto", "../../etc/passwd", UN_PNG)

    assert respuesta.status_code == 200
    assert ".." not in respuesta.json()["url"]
    assert respuesta.json()["url"].endswith(".png")


# ------------------------------------------------------------------- Servir


def test_sin_sesion_no_se_descarga_el_cv(client):
    url = _subir(client, "cv", "hoja.pdf", UN_PDF).json()["url"]

    assert client.get(url).status_code == 401


def test_con_sesion_si_se_descarga(client, reclutador_headers):
    url = _subir(client, "cv", "hoja.pdf", UN_PDF).json()["url"]

    respuesta = client.get(url, headers=reclutador_headers)

    assert respuesta.status_code == 200
    assert respuesta.content == UN_PDF


def test_la_ruta_publica_de_medios_no_sirve_el_cv(client):
    """La prueba que justifica todo lo demás.

    `/media` va sin autenticación a propósito. Si desde ahí se pudiera pedir
    `postulantes/<archivo>`, la carpeta privada no sería privada: bastaría con saber
    —o filtrar— el nombre.
    """
    url = _subir(client, "cv", "hoja.pdf", UN_PDF).json()["url"]
    nombre = url.rsplit("/", 1)[1]

    assert client.get(f"/api/v1/media/postulantes/{nombre}").status_code == 404


def test_la_ruta_publica_no_se_escapa_de_su_carpeta(client):
    """Con `..` tampoco: la comprobación es sobre la ruta ya resuelta."""
    assert client.get("/api/v1/media/../app/core/config.py").status_code == 404


def test_un_archivo_que_no_existe_da_404(client, reclutador_headers):
    assert client.get("/api/v1/archivos/postulantes/noexiste.pdf", headers=reclutador_headers).status_code == 404


def test_un_cv_que_el_lector_rechaza_no_deja_copia(client, tmp_path):
    """El orden importa: primero se lee, después se guarda.

    Al revés, un archivo que el lector rechaza —pasa del tamaño, es un `.doc`
    antiguo— ya habría dejado su copia en el volumen, y ninguna ficha apuntaría nunca
    a ella: basura que nadie borra.
    """
    enorme = b"x" * (16 * 1024 * 1024)

    respuesta = client.post("/api/v1/public/leer-cv", files={"file": ("cv.pdf", enorme, "application/pdf")})

    assert respuesta.status_code == 413
    assert not (tmp_path / "postulantes").exists()
