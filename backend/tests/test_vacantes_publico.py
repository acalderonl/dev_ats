from datetime import datetime, timedelta, timezone


def _crear_cargo(crear_cargo, unique_suffix) -> int:
    return crear_cargo(unique_suffix)["id"]


def _crear_vacante(client, reclutador_headers, cargo_id: int, titulo: str, fecha_limite: datetime):
    response = client.post(
        "/api/v1/vacantes",
        json={
            "titulo": titulo,
            "cargo_id": cargo_id,
            "descripcion": "Descripción de prueba",
            "fecha_limite": fecha_limite.isoformat(),
        },
        headers=reclutador_headers,
    )
    return response


def test_crear_vacante_genera_slug_unico(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = _crear_cargo(crear_cargo, unique_suffix)
    titulo = f"Vacante Test {unique_suffix}"
    fecha = datetime.now(timezone.utc) + timedelta(days=10)

    r1 = _crear_vacante(client, reclutador_headers, cargo_id, titulo, fecha)
    r2 = _crear_vacante(client, reclutador_headers, cargo_id, titulo, fecha)

    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["slug"] != r2.json()["slug"]


def test_vacante_activa_es_visible_publicamente(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = _crear_cargo(crear_cargo, unique_suffix)
    fecha = datetime.now(timezone.utc) + timedelta(days=5)
    vacante = _crear_vacante(client, reclutador_headers, cargo_id, f"Vacante Publica {unique_suffix}", fecha).json()

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")
    assert response.status_code == 200
    assert response.json()["titulo"] == vacante["titulo"]


def test_vacante_expirada_devuelve_410(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = _crear_cargo(crear_cargo, unique_suffix)
    fecha_pasada = datetime.now(timezone.utc) - timedelta(days=1)
    vacante = _crear_vacante(
        client, reclutador_headers, cargo_id, f"Vacante Expirada {unique_suffix}", fecha_pasada
    ).json()

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")
    assert response.status_code == 410


def test_postular_a_vacante_expirada_devuelve_410(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo_id = _crear_cargo(crear_cargo, unique_suffix)
    fecha_pasada = datetime.now(timezone.utc) - timedelta(days=1)
    vacante = _crear_vacante(
        client, reclutador_headers, cargo_id, f"Vacante Expirada Postular {unique_suffix}", fecha_pasada
    ).json()

    response = client.post(
        f"/api/v1/public/vacantes/{vacante['slug']}/postular",
        json={
            "nombres": "Juan",
            "apellidos": "Pérez",
            "cedula": f"17{unique_suffix[:8]}",
            "email": "juan.perez@example.com",
        },
    )
    assert response.status_code == 410
