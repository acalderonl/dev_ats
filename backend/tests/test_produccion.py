"""Lo que separa un despliegue seguro de uno que regala el acceso.

Estas pruebas existen porque el sistema va a estar en internet. Cada una comprueba una
puerta que hoy estaba abierta.
"""

import io

import pytest
from sqlalchemy import func, select

from app.core.config import Settings
from app.core.limites import LIMITES
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.seed import DEMO_USERS, run_seed, seed_roles


# --------------------------------------------------- El seed fuera de desarrollo


def _ajustes(**extra) -> Settings:
    return Settings(secret_key="una-clave-larga-de-pruebas-con-mas-de-32", **extra)


def test_el_entorno_por_defecto_es_desarrollo():
    assert _ajustes().es_produccion is False


@pytest.mark.parametrize("valor", ["prod", "PRODUCTION", "staging", ""])
def test_un_entorno_inventado_se_rechaza(valor):
    """Un `ENTORNO=prod` mal escrito no puede pasar por desarrollo en silencio."""
    with pytest.raises(ValueError):
        _ajustes(entorno=valor)


def test_en_produccion_no_se_crean_cuentas_de_demo(db_limpia, monkeypatch):
    """La prueba que justifica todo esto.

    `Demo1234!` está publicada en el repositorio. Si el seed la crea en un servidor con
    URL pública, cualquiera que lea el repositorio entra como super admin.
    """
    monkeypatch.setenv("ENTORNO", "produccion")
    monkeypatch.setenv("ADMIN_INICIAL_EMAIL", "jefe@anai.edu.ec")
    monkeypatch.setenv("ADMIN_INICIAL_PASSWORD", "una-clave-larga-de-verdad")
    from app.core.config import get_settings

    get_settings.cache_clear()

    try:
        run_seed(db_limpia)

        correos = set(db_limpia.scalars(select(Usuario.email)).all())
        de_demo = {email for email, *_ in DEMO_USERS}
        assert correos & de_demo == set(), "El seed creó cuentas de demo en producción"
        assert correos == {"jefe@anai.edu.ec"}
    finally:
        get_settings.cache_clear()


def test_en_produccion_sin_admin_inicial_no_se_crea_nadie(db_limpia, monkeypatch):
    """Sin administrador es un problema visible; con uno adivinable, no."""
    monkeypatch.setenv("ENTORNO", "produccion")
    monkeypatch.delenv("ADMIN_INICIAL_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_INICIAL_PASSWORD", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()

    try:
        run_seed(db_limpia)
        assert db_limpia.scalar(select(func.count()).select_from(Usuario)) == 0
    finally:
        get_settings.cache_clear()


def test_en_produccion_si_se_siembran_roles_y_catalogos(db_limpia, monkeypatch):
    """Control positivo: sin roles ni niveles de educación la aplicación no funciona.

    Lo que no debe viajar a producción son las cuentas y los cargos de ejemplo, no el
    andamiaje que el sistema necesita para arrancar.
    """
    monkeypatch.setenv("ENTORNO", "produccion")
    from app.core.config import get_settings

    get_settings.cache_clear()

    try:
        run_seed(db_limpia)
        assert db_limpia.scalar(select(func.count()).select_from(Rol)) == 3
    finally:
        get_settings.cache_clear()


def test_el_seed_no_recrea_una_cuenta_renombrada(db_limpia):
    """El fallo que se vio de verdad el 14 de octubre.

    Antes se comprobaba correo por correo, así que renombrar `admin@atsdemo.com` hacía
    que el siguiente arranque lo recreara con la contraseña publicada. Ahora el seed
    solo actúa en una base sin ningún usuario.
    """
    roles = seed_roles(db_limpia)
    db_limpia.add(
        Usuario(
            email="persona.real@anai.edu.ec",
            password_hash="x",
            nombres="Persona",
            apellidos="Real",
            rol_id=roles["super_admin"].id,
        )
    )
    db_limpia.commit()

    run_seed(db_limpia)

    correos = set(db_limpia.scalars(select(Usuario.email)).all())
    assert correos == {"persona.real@anai.edu.ec"}


# ------------------------------------------------------------------ CORS


def test_en_produccion_cors_no_incluye_localhost():
    """Si lo incluyera, una página local podría hablar con el servidor real."""
    ajustes = _ajustes(entorno="produccion", frontend_origin="https://ats.anai.edu.ec")

    origenes = ajustes.origenes_permitidos()

    assert origenes == ["https://ats.anai.edu.ec"]


def test_en_desarrollo_cors_si_incluye_localhost():
    """Control positivo: en local no hay que configurar nada."""
    assert "http://localhost:3000" in _ajustes().origenes_permitidos()


def test_cors_admite_varios_origenes_separados_por_comas():
    ajustes = _ajustes(entorno="produccion", frontend_origin="https://ats.anai.edu.ec, https://pruebas.anai.edu.ec/")

    assert ajustes.origenes_permitidos() == ["https://ats.anai.edu.ec", "https://pruebas.anai.edu.ec"]


# -------------------------------------------------- Límite de peticiones


def test_el_portal_publico_corta_al_pasarse(client):
    """Sin esto, `/leer-cv` es una factura abierta: cada llamada va a la API de Claude."""
    maximo, _ = LIMITES["leer_cv"]
    archivo = lambda: {"file": ("cv.txt", io.BytesIO(b"hola"), "text/plain")}  # noqa: E731

    codigos = [client.post("/api/v1/public/leer-cv", files=archivo()).status_code for _ in range(maximo + 2)]

    # Las primeras llegan al endpoint (y fallan por formato, que es otra cosa);
    # a partir del tope, el límite las para antes.
    assert 429 in codigos
    assert codigos.count(429) == 2


def test_el_limite_distingue_por_ip(client):
    """Un candidato no puede dejar sin servicio a los demás."""
    maximo, _ = LIMITES["leer_cv"]
    archivo = lambda: {"file": ("cv.txt", io.BytesIO(b"hola"), "text/plain")}  # noqa: E731

    for _ in range(maximo + 1):
        client.post("/api/v1/public/leer-cv", files=archivo(), headers={"X-Forwarded-For": "10.0.0.1"})

    otra_ip = client.post("/api/v1/public/leer-cv", files=archivo(), headers={"X-Forwarded-For": "10.0.0.2"})

    assert otra_ip.status_code != 429


def test_la_respuesta_dice_cuanto_esperar(client):
    """Un 429 sin `Retry-After` obliga a adivinar."""
    maximo, _ = LIMITES["leer_cv"]
    archivo = lambda: {"file": ("cv.txt", io.BytesIO(b"hola"), "text/plain")}  # noqa: E731

    respuesta = None
    for _ in range(maximo + 1):
        respuesta = client.post("/api/v1/public/leer-cv", files=archivo())

    assert respuesta.status_code == 429
    assert "Retry-After" in respuesta.headers
