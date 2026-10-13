def _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante) -> str:
    cargo = crear_cargo(unique_suffix)

    vacante = crear_vacante(cargo["id"])

    postulante = client.post(
        f"/api/v1/public/vacantes/{vacante['slug']}/postular",
        json={
            "nombres": "Ana",
            "apellidos": "Gómez",
            "cedula": f"18{unique_suffix[:8]}",
            "email": "ana.gomez@example.com",
        },
    ).json()

    postulaciones = client.get(
        "/api/v1/postulaciones", params={"vacante_id": vacante["id"]}, headers=reclutador_headers
    ).json()
    postulacion = next(p for p in postulaciones if p["postulante_id"] == postulante["id"])
    return postulacion["id"]


def test_no_puede_avanzar_sin_autorizacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    postulacion_id = _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante)

    response = client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "en_revision"},
        headers=reclutador_headers,
    )
    assert response.status_code == 403


def test_autorizar_y_avanzar_pipeline(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    postulacion_id = _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante)

    autorizar = client.post(f"/api/v1/postulaciones/{postulacion_id}/autorizar", headers=reclutador_headers)
    assert autorizar.status_code == 200
    assert autorizar.json()["estado_pipeline"] == "postulacion_revisada"
    assert autorizar.json()["autorizado_por"] is not None

    avanzar = client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "entrevista"},
        headers=reclutador_headers,
    )
    assert avanzar.status_code == 200
    assert avanzar.json()["estado_pipeline"] == "entrevista"


def test_no_puede_retroceder_etapa(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    postulacion_id = _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante)
    client.post(f"/api/v1/postulaciones/{postulacion_id}/autorizar", headers=reclutador_headers)
    client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "preseleccionado"},
        headers=reclutador_headers,
    )

    retroceso = client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "en_revision"},
        headers=reclutador_headers,
    )
    assert retroceso.status_code == 409


def test_puede_descartar_en_cualquier_momento(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    postulacion_id = _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante)
    client.post(f"/api/v1/postulaciones/{postulacion_id}/autorizar", headers=reclutador_headers)

    descartar = client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "descartado"},
        headers=reclutador_headers,
    )
    assert descartar.status_code == 200
    assert descartar.json()["estado_pipeline"] == "descartado"

    reactivar = client.patch(
        f"/api/v1/postulaciones/{postulacion_id}/pipeline-status",
        json={"estado_pipeline": "en_revision"},
        headers=reclutador_headers,
    )
    assert reactivar.status_code == 409


def test_evaluacion_requiere_postulacion_existente(client, entrevistador_headers, unique_suffix):
    response = client.post(
        "/api/v1/postulaciones/00000000-0000-0000-0000-000000000000/evaluaciones",
        json={"tipo_evaluacion": "Entrevista Técnica", "puntaje": 85, "observaciones": "Buen desempeño"},
        headers=entrevistador_headers,
    )
    assert response.status_code == 404


def test_registrar_evaluacion(
    client, reclutador_headers, entrevistador_headers, unique_suffix, crear_cargo, crear_vacante
):
    postulacion_id = _crear_postulacion(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante)
    client.post(f"/api/v1/postulaciones/{postulacion_id}/autorizar", headers=reclutador_headers)

    response = client.post(
        f"/api/v1/postulaciones/{postulacion_id}/evaluaciones",
        json={"tipo_evaluacion": "Prueba Psicométrica", "puntaje": 92.5, "observaciones": "Excelente"},
        headers=entrevistador_headers,
    )
    assert response.status_code == 201
    assert response.json()["puntaje"] == 92.5
