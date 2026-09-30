def test_crear_cargo_y_pregunta_filtro(client, reclutador_headers, unique_suffix):
    response = client.post(
        "/api/v1/cargos",
        json={"nombre": f"Cargo Test {unique_suffix}", "departamento": "QA", "descripcion": "Cargo de prueba"},
        headers=reclutador_headers,
    )
    assert response.status_code == 201, response.text
    cargo = response.json()
    assert cargo["activo"] is True

    pregunta_response = client.post(
        f"/api/v1/cargos/{cargo['id']}/preguntas-filtro",
        json={
            "pregunta": "¿Disponibilidad inmediata?",
            "tipo_respuesta": "booleano",
            "es_eliminatoria": True,
            "respuesta_correcta": "Sí",
        },
        headers=reclutador_headers,
    )
    assert pregunta_response.status_code == 201, pregunta_response.text

    listado = client.get(f"/api/v1/cargos/{cargo['id']}/preguntas-filtro")
    assert listado.status_code == 200
    assert len(listado.json()) == 1


def test_crear_cargo_sin_autenticacion_falla(client, unique_suffix):
    response = client.post(
        "/api/v1/cargos",
        json={"nombre": f"Cargo Sin Auth {unique_suffix}", "departamento": "QA", "descripcion": "x"},
    )
    assert response.status_code == 401


def test_listar_cargos_es_publico(client):
    response = client.get("/api/v1/cargos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
