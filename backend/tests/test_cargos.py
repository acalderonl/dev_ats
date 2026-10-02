def _crear_nombre(client, headers, nombre: str) -> int:
    respuesta = client.post("/api/v1/catalogos/nombres-cargo", json={"nombre": nombre}, headers=headers)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def test_crear_cargo_con_mision_y_actividades(client, reclutador_headers, unique_suffix):
    nombre_id = _crear_nombre(client, reclutador_headers, f"Jefe de Planta {unique_suffix}")

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "tiene_personal_a_cargo": True,
            "mision": "Garantizar que la planta produzca en los plazos comprometidos.",
            "actividades": [
                {"texto": "Planificar la producción semanal", "favorita": False},
                {"texto": "Supervisar al equipo de turno", "favorita": False},
            ],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 201, respuesta.text

    cargo = respuesta.json()
    assert cargo["nombre"] == f"Jefe de Planta {unique_suffix}"
    assert cargo["tiene_personal_a_cargo"] is True
    assert cargo["clasificacion"] is None
    assert [a["texto"] for a in cargo["actividades"]] == [
        "Planificar la producción semanal",
        "Supervisar al equipo de turno",
    ]
    assert cargo["activo"] is True


def test_las_actividades_en_blanco_no_se_guardan(client, reclutador_headers, unique_suffix):
    """La lista dinámica del formulario deja filas vacías; no deben llegar a la base."""
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Blancos {unique_suffix}")

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "actividades": [
                {"texto": "Actividad real", "favorita": False},
                {"texto": "", "favorita": False},
                {"texto": "   ", "favorita": False},
                {"texto": "Otra real", "favorita": False},
            ],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 201, respuesta.text
    assert [a["texto"] for a in respuesta.json()["actividades"]] == ["Actividad real", "Otra real"]


def test_las_actividades_favoritas_se_guardan_primero(client, reclutador_headers, unique_suffix):
    """La estrella sube la actividad al principio; dentro de cada grupo se respeta el orden."""
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Favoritas {unique_suffix}")

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "actividades": [
                {"texto": "Primera normal", "favorita": False},
                {"texto": "Destacada A", "favorita": True},
                {"texto": "Segunda normal", "favorita": False},
                {"texto": "Destacada B", "favorita": True},
            ],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 201, respuesta.text

    textos = [a["texto"] for a in respuesta.json()["actividades"]]
    assert textos == ["Destacada A", "Destacada B", "Primera normal", "Segunda normal"]


def test_experiencia_y_competencias_se_guardan(client, reclutador_headers, unique_suffix):
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Completo {unique_suffix}")
    competencia = client.post(
        "/api/v1/competencias",
        json={"nombre": f"Excel avanzado {unique_suffix}", "tipo": "academico"},
        headers=reclutador_headers,
    ).json()

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "experiencia_requerida": "3_a_5",
            "competencias": [{"competencia_id": competencia["id"], "requerido": False, "deseado": True}],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 201, respuesta.text

    cargo = respuesta.json()
    assert cargo["experiencia_requerida"] == "3_a_5"
    assert len(cargo["competencias"]) == 1
    assert cargo["competencias"][0]["nombre"] == f"Excel avanzado {unique_suffix}"
    assert cargo["competencias"][0]["deseado"] is True
    assert cargo["competencias"][0]["requerido"] is False


def test_educacion_formal_se_guarda(client, reclutador_headers, unique_suffix):
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Educacion {unique_suffix}")
    niveles = client.get("/api/v1/catalogos/niveles-educacion", headers=reclutador_headers).json()
    areas = client.get("/api/v1/catalogos/areas-academicas", headers=reclutador_headers).json()
    assert niveles and areas, "el seed debe dejar sembrados los catálogos de educación"

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "nivel_educacion_id": niveles[0]["id"],
            "estado_educacion": "en_curso",
            "area_academica_id": areas[0]["id"],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 201, respuesta.text

    cargo = respuesta.json()
    assert cargo["nivel_educacion"] == niveles[0]["nombre"]
    assert cargo["estado_educacion"] == "en_curso"
    assert cargo["area_academica"] == areas[0]["nombre"]


def test_estado_educacion_invalido_se_rechaza(client, reclutador_headers, unique_suffix):
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Edu Mal {unique_suffix}")
    respuesta = client.post(
        "/api/v1/cargos",
        json={"nombre_id": nombre_id, "estado_educacion": "a_medias"},
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_una_competencia_no_puede_ser_requerida_y_deseada(client, reclutador_headers, unique_suffix):
    """Son excluyentes: o es requisito o es deseable."""
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Excluyente {unique_suffix}")
    competencia = client.post(
        "/api/v1/competencias",
        json={"nombre": f"Negociación {unique_suffix}", "tipo": "blanda"},
        headers=reclutador_headers,
    ).json()

    respuesta = client.post(
        "/api/v1/cargos",
        json={
            "nombre_id": nombre_id,
            "competencias": [{"competencia_id": competencia["id"], "requerido": True, "deseado": True}],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_experiencia_invalida_se_rechaza(client, reclutador_headers, unique_suffix):
    nombre_id = _crear_nombre(client, reclutador_headers, f"Cargo Exp {unique_suffix}")
    respuesta = client.post(
        "/api/v1/cargos",
        json={"nombre_id": nombre_id, "experiencia_requerida": "20_anios"},
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 422


def test_editar_cargo_reemplaza_su_contenido(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo = crear_cargo(unique_suffix, mision="Misión vieja")
    competencia = client.post(
        "/api/v1/competencias",
        json={"nombre": f"Oratoria {unique_suffix}", "tipo": "blanda"},
        headers=reclutador_headers,
    ).json()

    respuesta = client.put(
        f"/api/v1/cargos/{cargo['id']}",
        json={
            "nombre_id": cargo["nombre_id"],
            "mision": "Misión nueva",
            "actividades": [{"texto": "Actividad editada", "favorita": True}],
            "experiencia_requerida": "hasta_1",
            "competencias": [{"competencia_id": competencia["id"], "requerido": False, "deseado": True}],
        },
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 200, respuesta.text

    editado = respuesta.json()
    assert editado["id"] == cargo["id"]
    assert editado["mision"] == "Misión nueva"
    assert [a["texto"] for a in editado["actividades"]] == ["Actividad editada"]
    assert editado["experiencia_requerida"] == "hasta_1"
    assert len(editado["competencias"]) == 1
    assert editado["competencias"][0]["deseado"] is True


def test_editar_no_duplica_competencias(client, reclutador_headers, unique_suffix, crear_cargo):
    """Guardar dos veces la misma competencia no debe crear dos filas en la tabla puente."""
    cargo = crear_cargo(unique_suffix)
    competencia = client.post(
        "/api/v1/competencias",
        json={"nombre": f"Resiliencia {unique_suffix}", "tipo": "blanda"},
        headers=reclutador_headers,
    ).json()

    cuerpo = {
        "nombre_id": cargo["nombre_id"],
        "competencias": [{"competencia_id": competencia["id"], "requerido": True, "deseado": False}],
    }
    client.put(f"/api/v1/cargos/{cargo['id']}", json=cuerpo, headers=reclutador_headers)
    segunda = client.put(f"/api/v1/cargos/{cargo['id']}", json=cuerpo, headers=reclutador_headers)

    assert segunda.status_code == 200
    assert len(segunda.json()["competencias"]) == 1


def test_editar_un_cargo_inexistente_da_404(client, reclutador_headers):
    respuesta = client.put("/api/v1/cargos/999999", json={"nombre_id": 1}, headers=reclutador_headers)
    assert respuesta.status_code == 404


def test_editar_requiere_autenticacion(client, unique_suffix, crear_cargo):
    cargo = crear_cargo(unique_suffix)
    respuesta = client.put(f"/api/v1/cargos/{cargo['id']}", json={"nombre_id": cargo["nombre_id"]})
    assert respuesta.status_code == 401


def test_crear_cargo_con_nombre_inexistente_falla(client, reclutador_headers):
    respuesta = client.post("/api/v1/cargos", json={"nombre_id": 999999}, headers=reclutador_headers)
    assert respuesta.status_code == 400
    assert "catálogo" in respuesta.json()["detail"]


def test_crear_cargo_con_clasificacion(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo = crear_cargo(unique_suffix, clasificacion="Operaciones")
    assert cargo["clasificacion"] == f"Operaciones {unique_suffix}"
    assert cargo["clasificacion_id"] is not None


def test_crear_cargo_y_pregunta_filtro(client, reclutador_headers, unique_suffix, crear_cargo):
    cargo = crear_cargo(unique_suffix)

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


def test_crear_cargo_sin_autenticacion_falla(client):
    respuesta = client.post("/api/v1/cargos", json={"nombre_id": 1})
    assert respuesta.status_code == 401


def test_listar_cargos_es_publico(client):
    respuesta = client.get("/api/v1/cargos")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)
