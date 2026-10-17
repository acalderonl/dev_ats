"""Conocimientos académicos y habilidades blandas, y las defensas contra duplicarlos."""


def _crear(client, headers, nombre, tipo="academico"):
    return client.post("/api/v1/competencias", json={"nombre": nombre, "tipo": tipo}, headers=headers)


def test_crear_y_buscar(client, reclutador_headers, unique_suffix):
    nombre = f"Contabilidad de costos {unique_suffix}"
    creada = _crear(client, reclutador_headers, nombre)
    assert creada.status_code == 201, creada.text
    assert creada.json()["usos"] == 0

    encontrada = client.get(
        "/api/v1/competencias", params={"tipo": "academico", "q": "contabilidad"}, headers=reclutador_headers
    )
    assert encontrada.status_code == 200
    assert any(c["nombre"] == nombre for c in encontrada.json())


def test_la_misma_escrita_distinto_no_se_duplica(client, reclutador_headers, unique_suffix):
    """Tildes y mayúsculas no deben crear un registro nuevo: devuelve el que ya existe."""
    original = _crear(client, reclutador_headers, f"Programación Orientada a Objetos {unique_suffix}")
    assert original.status_code == 201

    repetida = _crear(client, reclutador_headers, f"programacion orientada a objetos {unique_suffix}")
    assert repetida.status_code == 201
    assert repetida.json()["id"] == original.json()["id"]
    assert repetida.json()["nombre"] == original.json()["nombre"]


def test_la_busqueda_sugiere_las_parecidas(client, reclutador_headers, unique_suffix):
    """El caso que motiva todo esto: evitar 'Trabajo en equipos' junto a 'Trabajo en equipo'."""
    _crear(client, reclutador_headers, f"Trabajo en equipo {unique_suffix}", tipo="blanda")

    respuesta = client.get(
        "/api/v1/competencias",
        params={"tipo": "blanda", "q": f"trabajo en equipos {unique_suffix}"},
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 200
    resultados = respuesta.json()
    assert len(resultados) >= 1, "la parecida debería aparecer aunque no se escriba igual"
    assert resultados[0]["similitud"] > 0.5


def test_los_tipos_no_se_mezclan(client, reclutador_headers, unique_suffix):
    nombre = f"Liderazgo {unique_suffix}"
    _crear(client, reclutador_headers, nombre, tipo="blanda")

    academicas = client.get(
        "/api/v1/competencias", params={"tipo": "academico", "q": nombre}, headers=reclutador_headers
    ).json()
    assert all(c["nombre"] != nombre for c in academicas)


def test_no_se_puede_eliminar_una_en_uso(client, reclutador_headers, unique_suffix, crear_cargo):
    competencia = _crear(client, reclutador_headers, f"SQL {unique_suffix}").json()
    crear_cargo(
        unique_suffix,
        competencias=[{"competencia_id": competencia["id"], "requerido": True, "deseado": False}],
    )

    respuesta = client.delete(f"/api/v1/competencias/{competencia['id']}", headers=reclutador_headers)
    assert respuesta.status_code == 409

    listado = client.get(
        "/api/v1/competencias", params={"tipo": "academico", "q": f"SQL {unique_suffix}"}, headers=reclutador_headers
    ).json()
    assert listado[0]["usos"] == 1


def test_requiere_autenticacion(client):
    assert client.get("/api/v1/competencias", params={"tipo": "academico"}).status_code == 401


# ------------------------------------------- Sugerencias por clasificación


def test_agrupa_las_competencias_por_la_clasificacion_del_cargo(client, reclutador_headers, unique_suffix, crear_cargo):
    """Al crear un cargo de un área interesa ver qué piden los otros cargos de esa área."""
    cargo = crear_cargo(unique_suffix, clasificacion="Ingeniería")
    competencia = client.post(
        "/api/v1/competencias",
        json={"tipo": "academico", "nombre": f"Termodinámica {unique_suffix[:5]}"},
        headers=reclutador_headers,
    ).json()
    client.put(
        f"/api/v1/cargos/{cargo['id']}",
        json={
            "nombre_id": cargo["nombre_id"],
            "clasificacion_id": cargo["clasificacion_id"],
            "competencias": [{"competencia_id": competencia["id"], "requerido": True, "deseado": False}],
        },
        headers=reclutador_headers,
    )

    grupos = client.get(
        "/api/v1/competencias/por-clasificacion", params={"tipo": "academico"}, headers=reclutador_headers
    ).json()

    mio = next(g for g in grupos if g["clasificacion_id"] == cargo["clasificacion_id"])
    assert competencia["nombre"] in [c["nombre"] for c in mio["competencias"]]


def test_no_devuelve_grupos_vacios(client, reclutador_headers, unique_suffix, crear_cargo):
    """Un botón que al abrirse no muestra nada es una promesa incumplida.

    Se crea un cargo con clasificación pero SIN competencias: su clasificación no debe
    aparecer entre los grupos.
    """
    cargo = crear_cargo(unique_suffix, clasificacion="Sin competencias")

    grupos = client.get(
        "/api/v1/competencias/por-clasificacion", params={"tipo": "academico"}, headers=reclutador_headers
    ).json()

    assert cargo["clasificacion_id"] not in [g["clasificacion_id"] for g in grupos]


def test_separa_academicas_de_blandas(client, reclutador_headers, unique_suffix, crear_cargo):
    """Las secciones 5 y 6 del modal no pueden ofrecerse lo del otro tipo."""
    cargo = crear_cargo(unique_suffix, clasificacion="Mixta")
    blanda = client.post(
        "/api/v1/competencias",
        json={"tipo": "blanda", "nombre": f"Escucha activa {unique_suffix[:5]}"},
        headers=reclutador_headers,
    ).json()
    client.put(
        f"/api/v1/cargos/{cargo['id']}",
        json={
            "nombre_id": cargo["nombre_id"],
            "clasificacion_id": cargo["clasificacion_id"],
            "competencias": [{"competencia_id": blanda["id"], "requerido": True, "deseado": False}],
        },
        headers=reclutador_headers,
    )

    academicos = client.get(
        "/api/v1/competencias/por-clasificacion", params={"tipo": "academico"}, headers=reclutador_headers
    ).json()
    blandas = client.get(
        "/api/v1/competencias/por-clasificacion", params={"tipo": "blanda"}, headers=reclutador_headers
    ).json()

    assert cargo["clasificacion_id"] not in [g["clasificacion_id"] for g in academicos]
    grupo = next(g for g in blandas if g["clasificacion_id"] == cargo["clasificacion_id"])
    assert blanda["nombre"] in [c["nombre"] for c in grupo["competencias"]]


def test_un_tipo_invalido_se_rechaza(client, reclutador_headers):
    respuesta = client.get(
        "/api/v1/competencias/por-clasificacion", params={"tipo": "inventado"}, headers=reclutador_headers
    )
    assert respuesta.status_code == 422
