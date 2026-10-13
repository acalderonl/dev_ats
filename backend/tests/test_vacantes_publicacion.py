"""La vacante como publicación: condiciones, campos libres, estados y alcance."""

from datetime import datetime, timedelta, timezone

import pytest


def test_guarda_remuneracion_horario_y_contrato(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    tipos = client.get("/api/v1/catalogos/tipos-contrato", headers=reclutador_headers).json()

    vacante = crear_vacante(
        cargo_id,
        remuneracion="1250.50",
        jornada_horas="8",
        hora_entrada="09:00:00",
        hora_salida="17:00:00",
        tipo_contrato_id=tipos[0]["id"],
    )

    assert vacante["remuneracion"] == "1250.50"
    assert vacante["hora_entrada"] == "09:00:00"
    assert vacante["hora_salida"] == "17:00:00"
    assert vacante["tipo_contrato_nombre"] == tipos[0]["nombre"]


def test_remuneracion_negativa_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "remuneracion": "-100",
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_entrada_y_salida_no_pueden_coincidir(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "hora_entrada": "09:00:00",
            "hora_salida": "09:00:00",
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_guarda_campos_personalizados(client, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]

    vacante = crear_vacante(
        cargo_id,
        campos_personalizados=[
            {"etiqueta": "Ciudad", "valor": "Quito"},
            {"etiqueta": "Modalidad", "valor": "Híbrida"},
        ],
    )

    assert [c["etiqueta"] for c in vacante["campos_personalizados"]] == ["Ciudad", "Modalidad"]
    assert vacante["campos_personalizados"][0]["valor"] == "Quito"


def test_campos_personalizados_con_etiqueta_repetida_se_rechazan(
    client, reclutador_headers, unique_suffix, crear_cargo
):
    """Dos campos "Ciudad" harían ambigua la lectura del post."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "campos_personalizados": [
                {"etiqueta": "Ciudad", "valor": "Quito"},
                {"etiqueta": "ciudad", "valor": "Guayaquil"},
            ],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_campo_personalizado_sin_etiqueta_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "campos_personalizados": [{"etiqueta": "   ", "valor": "algo"}],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


@pytest.mark.parametrize("estado", ["en_proceso", "activa", "ACTIVA", ""])
def test_estado_invalido_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo, estado):
    """'activa' incluido: es el vocabulario viejo y ya no vale."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "estado": estado,
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_interna_sin_destinatarios_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo):
    """Una vacante interna sin a quién mandarla no llega a nadie."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "visibilidad": "interna",
            "destinatarios_internos": [],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_no_se_puede_abrir_vacante_de_cargo_desactivado(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo = crear_cargo(unique_suffix)
    client.patch(f"/api/v1/cargos/{cargo['id']}/toggle-activo", headers=reclutador_headers)

    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo["id"],
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        },
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    assert "desactivado" in respuesta.json()["detail"]


def test_programar_sin_fecha_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id)

    respuesta = client.patch(
        f"/api/v1/vacantes/{vacante['id']}/post-estado",
        json={"post_estado": "programado"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    assert "fecha" in respuesta.json()["detail"]


def test_programar_con_fecha_funciona(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """Control positivo del anterior."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    cuando = datetime.now(timezone.utc) + timedelta(days=2)
    vacante = crear_vacante(cargo_id, post_programado_para=cuando.isoformat())

    respuesta = client.patch(
        f"/api/v1/vacantes/{vacante['id']}/post-estado",
        json={"post_estado": "programado"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["post_estado"] == "programado"


def test_programar_en_el_pasado_se_rechaza(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = crear_cargo(unique_suffix)["id"]
    ayer = datetime.now(timezone.utc) - timedelta(days=1)
    respuesta = client.post(
        "/api/v1/vacantes",
        json={
            "cargo_id": cargo_id,
            "descripcion": "x",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "post_programado_para": ayer.isoformat(),
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_publicado_no_se_pone_a_mano(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """Si se pudiera, la pantalla diría que salió algo que nunca salió."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id)

    respuesta = client.patch(
        f"/api/v1/vacantes/{vacante['id']}/post-estado",
        json={"post_estado": "publicado"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400


def test_vista_previa_incluye_condiciones_y_enlace(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(
        cargo_id,
        asunto="Buscamos talento",
        remuneracion="900.00",
        campos_personalizados=[{"etiqueta": "Ciudad", "valor": "Quito"}],
    )

    previa = client.get(f"/api/v1/vacantes/{vacante['id']}/vista-previa", headers=reclutador_headers).json()

    assert previa["asunto"] == "Buscamos talento"
    assert "900.00" in previa["cuerpo"]
    assert "Ciudad: Quito" in previa["cuerpo"]
    assert vacante["slug"] in previa["enlace_para_postular"]
    assert previa["caracteres"] == len(previa["cuerpo"])


def test_publicar_sin_credenciales_queda_marcado_como_simulado(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    """Sin configurar LinkedIn no se miente: se dice que fue simulado."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id)

    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=reclutador_headers)

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["simulado"] is True
    assert cuerpo["post_estado"] == "publicado"
    assert "simulado" in cuerpo["linkedin_post_id"]


def test_vacante_interna_no_se_publica_en_linkedin(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id, visibilidad="interna", destinatarios_internos=["alguien@empresa.com"])

    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/publicar-linkedin", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "interna" in respuesta.json()["detail"]


def test_vacante_publica_no_tiene_envio_interno(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id, visibilidad="publica")

    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/enviar-interno", headers=reclutador_headers)

    assert respuesta.status_code == 400


def test_editar_no_cambia_el_slug(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """El enlace ya está repartido: editar la vacante no puede romperlo."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id)

    actualizada = client.put(
        f"/api/v1/vacantes/{vacante['id']}",
        json={
            "cargo_id": cargo_id,
            "descripcion": "Descripción cambiada del todo",
            "fecha_limite": (datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
            "estado": "abierta",
        },
        headers=reclutador_headers,
    ).json()

    assert actualizada["slug"] == vacante["slug"]
    assert actualizada["descripcion"] == "Descripción cambiada del todo"
