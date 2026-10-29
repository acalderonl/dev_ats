"""Conectar LinkedIn pegando un token del generador del portal.

El camino con OAuth necesita Client Secret y una Redirect URI registrada que coincida
carácter por carácter; con un token ya emitido no hace falta ninguna de las dos. Lo que
hay que proteger: que no se guarde un token inservible, y que tenerlo baste para
publicar de verdad —si no, se simularía la publicación teniendo con qué hacerla—.
"""

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.services import linkedin_service

UN_TOKEN = "AQX" + "x" * 40


class _RespuestaFalsa:
    def __init__(self, status_code: int, cuerpo: dict):
        self.status_code = status_code
        self._cuerpo = cuerpo

    def json(self) -> dict:
        return self._cuerpo

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)  # type: ignore[arg-type]


@pytest.fixture
def linkedin_responde(monkeypatch):
    """Sustituye la llamada a LinkedIn: las pruebas no salen a internet."""

    def _configurar(status_code: int, cuerpo: dict):
        class ClienteFalso:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def get(self, *_args, **_kwargs):
                return _RespuestaFalsa(status_code, cuerpo)

        monkeypatch.setattr(linkedin_service.httpx, "Client", lambda **_: ClienteFalso())

    return _configurar


# --------------------------------------------------------- Guardar el token


def test_un_token_bueno_deja_la_cuenta_conectada(client, reclutador_headers, linkedin_responde):
    linkedin_responde(200, {"sub": "ABC123", "name": "Alejandra Torres"})

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["cuenta_conectada"] is True
    assert cuerpo["nombre_en_linkedin"] == "Alejandra Torres"


def test_no_hacen_falta_client_id_ni_secret(client, reclutador_headers, linkedin_responde):
    """Es el motivo entero de este camino: sin credenciales de aplicación."""
    linkedin_responde(200, {"sub": "ABC123", "name": "Alejandra Torres"})

    client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )

    estado = client.get("/api/v1/configuracion/linkedin/estado", headers=reclutador_headers).json()
    assert estado["credenciales_configuradas"] is False
    assert estado["cuenta_conectada"] is True


def test_un_token_rechazado_no_se_guarda(client, reclutador_headers, linkedin_responde):
    """Mejor decirlo al pegarlo que al intentar publicar una vacante."""
    linkedin_responde(401, {})

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    estado = client.get("/api/v1/configuracion/linkedin/estado", headers=reclutador_headers).json()
    assert estado["cuenta_conectada"] is False


def test_un_token_sin_openid_no_se_guarda(client, reclutador_headers, linkedin_responde):
    """Sin `sub` no se sabe en qué muro publicar."""
    linkedin_responde(200, {"name": "Alguien"})

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    assert "openid" in respuesta.json()["detail"]


def test_los_saltos_de_linea_del_portal_no_rompen_el_token(client, reclutador_headers, linkedin_responde):
    """El generador lo muestra partido en varias líneas; al copiarlo se cuelan saltos."""
    linkedin_responde(200, {"sub": "ABC123", "name": "Alejandra Torres"})

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": "AQX\nxxxxxxxxxxxxxxxx  xxxxxxxxxxxxxxxxxxxxxx\n"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 200


def test_un_entrevistador_no_conecta_linkedin(client, linkedin_responde, entrevistador_headers):
    linkedin_responde(200, {"sub": "ABC123", "name": "Quien sea"})

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=entrevistador_headers,
    )

    assert respuesta.status_code == 403


# ------------------------------------------------- Lo que cambia al publicar


def test_con_token_pegado_se_publica_de_verdad_sin_credenciales(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, linkedin_responde, monkeypatch
):
    """Lo que de verdad importa de este cambio.

    Antes se miraba `esta_configurado` primero, así que sin Client ID/Secret la
    publicación se simulaba **aunque hubiera un token con el que publicar**.
    """
    linkedin_responde(200, {"sub": "ABC123", "name": "Alejandra Torres"})
    client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )
    monkeypatch.setattr(linkedin_service, "publicar_en_el_muro", lambda **_: "urn:li:share:7777")

    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    cuerpo = client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=reclutador_headers).json()

    assert cuerpo["simulado"] is False
    assert cuerpo["linkedin_post_id"] == "urn:li:share:7777"


def test_sin_token_y_sin_credenciales_sigue_simulando(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    """El modo simulado no se pierde: es lo que evita aparentar que algo salió."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")

    cuerpo = client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=reclutador_headers).json()

    assert cuerpo["simulado"] is True


def test_con_el_token_caducado_no_se_simula_sino_que_se_avisa(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante, linkedin_responde
):
    """Simular aquí sería mentir dos veces: ni publicó, ni está desconectado."""
    from app.core.database import SessionLocal
    from app.models.vacante import TokenLinkedIn

    linkedin_responde(200, {"sub": "ABC123", "name": "Alejandra Torres"})
    client.post(
        "/api/v1/configuracion/linkedin/token",
        json={"access_token": UN_TOKEN},
        headers=reclutador_headers,
    )

    # Sesión propia y corta: envejecer el token con una transacción abierta de otra
    # fixture bloquearía las escrituras del cliente contra la misma fila.
    with SessionLocal() as sesion:
        token = sesion.query(TokenLinkedIn).one()
        token.expira_en = datetime.now(timezone.utc) - timedelta(days=1)
        sesion.commit()

    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "caducó" in respuesta.json()["detail"]
