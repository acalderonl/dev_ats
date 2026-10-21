"""Configuración de las pruebas.

🔴 FUGA CERO: las pruebas corren contra una base propia (`ats_test_db`), nunca contra la
de desarrollo. Antes de este archivo cada `pytest` dejaba cargos, postulantes y usuarios
de prueba en la base real, y acababan saliendo en pantalla.

El cambio de `DATABASE_URL` ocurre ANTES de importar la aplicación, porque el motor de
SQLAlchemy se crea al importar `app.core.database`: si se importara primero, apuntaría a
la base equivocada y ya no habría forma de cambiarlo.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2

_URL_DESARROLLO = os.environ.get("DATABASE_URL", "postgresql://ats_user:ats_password@db:5432/ats_db")
_BASE_DE_PRUEBAS = "ats_test_db"
_RAIZ = _URL_DESARROLLO.rsplit("/", 1)[0]


def _crear_base_de_pruebas_si_no_existe() -> None:
    conexion = psycopg2.connect(_URL_DESARROLLO)
    conexion.autocommit = True
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (_BASE_DE_PRUEBAS,))
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE DATABASE "{_BASE_DE_PRUEBAS}"')
    finally:
        conexion.close()


_crear_base_de_pruebas_si_no_existe()
os.environ["DATABASE_URL"] = f"{_RAIZ}/{_BASE_DE_PRUEBAS}"

# `SECRET_KEY` ya no tiene valor por defecto: sin esto la aplicación no importa. Se fija
# aquí, igual que la base, antes de importarla. Es un valor propio de las pruebas: no
# sirve para firmar nada fuera de aquí y no debe parecerse al de desarrollo.
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-" + uuid.uuid4().hex)

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import DEMO_USERS  # noqa: E402


@pytest.fixture(autouse=True)
def _sin_peticiones_contadas():
    """Cada prueba arranca con el contador de peticiones a cero.

    El límite del portal público vive en memoria del proceso, así que se arrastra entre
    casos: sin esto, las pruebas del pipeline —que postulan varias veces desde la misma
    "IP"— agotaban la cuota y las últimas recibían un 429 en vez de crear nada.

    Es el mismo tipo de fuga que `configuracion`: estado global que no se limpia solo.
    """
    from app.core.limites import reiniciar

    reiniciar()
    yield
    reiniciar()


@pytest.fixture(autouse=True)
def _configuracion_vacia():
    """Cada prueba arranca sin nada configurado.

    Casi todas las tablas se pueden compartir entre pruebas porque cada una crea sus
    propias filas con un sufijo único. `configuracion` no: es clave-valor **global**,
    así que solo hay un `linkedin_client_id` para toda la suite. Sin esto, una prueba
    que configura LinkedIn hace que otra, que comprueba el modo simulado, vea
    credenciales y tome el camino equivocado.

    Es además el estado real de una instalación recién puesta, que es desde donde
    conviene que empiece cada prueba.
    """
    yield
    with engine.begin() as conexion:
        conexion.execute(text("DELETE FROM configuracion"))
        conexion.execute(text("DELETE FROM tokens_linkedin"))


@pytest.fixture(scope="session", autouse=True)
def _base_limpia():
    """Cada ejecución arranca con la base de pruebas vacía y migrada.

    El esquema se construye con **las migraciones de Alembic**, no con `create_all`. Es más
    lento, pero `create_all` solo conoce los modelos: se saltaría todo lo que vive únicamente
    en una migración (extensiones como `pg_trgm`, índices especiales, conversiones de datos),
    y entonces las pruebas pasarían sobre un esquema que no es el que tendrá producción.
    """
    if _BASE_DE_PRUEBAS not in str(engine.url):
        raise RuntimeError(
            f"Las pruebas apuntan a '{engine.url}', que no es la base de pruebas. "
            "Se aborta para no borrar datos de desarrollo."
        )

    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conexion:
        # Sin esto Alembic creería que la base ya está al día y no aplicaría nada.
        conexion.execute(text("DROP TABLE IF EXISTS alembic_version"))

    configuracion = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    configuracion.set_main_option("sqlalchemy.url", str(engine.url))
    command.upgrade(configuracion, "head")
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture()
def crear_cargo(client: TestClient, reclutador_headers: dict[str, str]):
    """Crea un cargo listo para usar y devuelve su JSON.

    Desde la migración 0002 el nombre del cargo vive en un catálogo, así que crear un
    cargo son dos pasos. El contrato se centraliza aquí para no repetirlo en cada prueba
    que solo necesita un cargo de apoyo.
    """

    def _crear(sufijo: str, *, clasificacion: str | None = None, **campos):
        respuesta_nombre = client.post(
            "/api/v1/catalogos/nombres-cargo",
            json={"nombre": f"Cargo Test {sufijo}"},
            headers=reclutador_headers,
        )
        assert respuesta_nombre.status_code == 201, respuesta_nombre.text

        clasificacion_id = None
        if clasificacion is not None:
            respuesta_clasificacion = client.post(
                "/api/v1/catalogos/clasificaciones",
                json={"nombre": f"{clasificacion} {sufijo}"},
                headers=reclutador_headers,
            )
            assert respuesta_clasificacion.status_code == 201, respuesta_clasificacion.text
            clasificacion_id = respuesta_clasificacion.json()["id"]

        payload = {
            "nombre_id": respuesta_nombre.json()["id"],
            "clasificacion_id": clasificacion_id,
            **campos,
        }
        respuesta = client.post("/api/v1/cargos", json=payload, headers=reclutador_headers)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[0]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def reclutador_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[1]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def entrevistador_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[2]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def crear_vacante(client: TestClient, reclutador_headers: dict[str, str]):
    """Crea una vacante y devuelve su JSON.

    Desde la migración 0006 la vacante nace en **borrador** y el título sale del cargo,
    no del payload. Casi toda prueba que usa una vacante la quiere visible, así que el
    valor por defecto aquí es `abierta`: pedir el estado en cada llamada escondería la
    intención detrás de ruido.

    Centralizado por lo aprendido con los cargos: cuando el contrato cambió, el arreglo
    fue un archivo en vez de cuatro.
    """

    def _crear(cargo_id: int, *, dias_de_plazo: int = 10, estado: str = "abierta", **campos):
        fecha = datetime.now(timezone.utc) + timedelta(days=dias_de_plazo)
        cuerpo = {
            "cargo_id": cargo_id,
            "descripcion": "Descripción de prueba",
            "fecha_limite": fecha.isoformat(),
            "estado": estado,
            **campos,
        }
        respuesta = client.post("/api/v1/vacantes", json=cuerpo, headers=reclutador_headers)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest.fixture()
def db_limpia():
    """Una base sin usuarios ni roles, para probar el seed como en una instalación nueva.

    Todo ocurre dentro de una transacción que **se deshace al terminar**. La suite
    comparte una sola base: si estos borrados se confirmaran, el resto de las pruebas
    se quedaría sin los usuarios de demo con los que inicia sesión.

    `join_transaction_mode="create_savepoint"` es lo que lo hace posible: el seed llama
    a `commit()` por dentro, y sin esto confirmaría la transacción externa junto con
    los borrados.
    """
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        # En orden de dependencia: lo que apunta a usuarios, antes que usuarios.
        for tabla in (
            "evaluaciones",
            "postulaciones",
            "vacantes",
            "tokens_linkedin",
            "usuario_permisos",
            "rol_permisos",
            "usuarios",
            "roles",
        ):
            sesion.execute(text(f"DELETE FROM {tabla}"))
        sesion.flush()
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()
