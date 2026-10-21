"""Los catálogos que alimentan los selectores del formulario de cargo."""


def test_crear_y_listar(client, reclutador_headers, unique_suffix):
    nombre = f"Clasificación {unique_suffix}"
    creado = client.post("/api/v1/catalogos/clasificaciones", json={"nombre": nombre}, headers=reclutador_headers)
    assert creado.status_code == 201, creado.text
    assert creado.json()["activo"] is True
    assert creado.json()["en_uso"] is False

    listado = client.get("/api/v1/catalogos/clasificaciones", headers=reclutador_headers)
    assert listado.status_code == 200
    assert any(i["nombre"] == nombre for i in listado.json())


def test_nombre_duplicado_devuelve_409(client, reclutador_headers, unique_suffix):
    payload = {"nombre": f"Repetido {unique_suffix}"}
    primero = client.post("/api/v1/catalogos/nombres-cargo", json=payload, headers=reclutador_headers)
    assert primero.status_code == 201

    segundo = client.post("/api/v1/catalogos/nombres-cargo", json=payload, headers=reclutador_headers)
    assert segundo.status_code == 409


def test_renombrar(client, reclutador_headers, unique_suffix):
    creado = client.post(
        "/api/v1/catalogos/nombres-cargo",
        json={"nombre": f"Antiguo {unique_suffix}"},
        headers=reclutador_headers,
    ).json()

    nuevo_nombre = f"Nuevo {unique_suffix}"
    respuesta = client.put(
        f"/api/v1/catalogos/nombres-cargo/{creado['id']}",
        json={"nombre": nuevo_nombre},
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == nuevo_nombre


def test_un_elemento_en_uso_no_se_puede_eliminar(client, reclutador_headers, unique_suffix, crear_cargo):
    """Borrar algo que un cargo usa dejaría el cargo sin nombre: el backend lo impide."""
    cargo = crear_cargo(unique_suffix)

    listado = client.get("/api/v1/catalogos/nombres-cargo", headers=reclutador_headers).json()
    en_uso = next(i for i in listado if i["id"] == cargo["nombre_id"])
    assert en_uso["en_uso"] is True

    respuesta = client.delete(f"/api/v1/catalogos/nombres-cargo/{cargo['nombre_id']}", headers=reclutador_headers)
    assert respuesta.status_code == 409
    assert "No se puede eliminar" in respuesta.json()["detail"]


def test_un_elemento_sin_uso_si_se_elimina(client, reclutador_headers, unique_suffix):
    creado = client.post(
        "/api/v1/catalogos/clasificaciones",
        json={"nombre": f"Desechable {unique_suffix}"},
        headers=reclutador_headers,
    ).json()

    respuesta = client.delete(f"/api/v1/catalogos/clasificaciones/{creado['id']}", headers=reclutador_headers)
    assert respuesta.status_code == 204

    listado = client.get("/api/v1/catalogos/clasificaciones", headers=reclutador_headers).json()
    assert all(i["id"] != creado["id"] for i in listado)


def test_desactivar_no_borra(client, reclutador_headers, unique_suffix, crear_cargo):
    """Alternativa a borrar cuando algo está en uso: deja de ofrecerse, pero sigue existiendo."""
    cargo = crear_cargo(unique_suffix)

    respuesta = client.put(
        f"/api/v1/catalogos/nombres-cargo/{cargo['nombre_id']}",
        json={"activo": False},
        headers=reclutador_headers,
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False

    cargos = client.get("/api/v1/cargos").json()
    sigue = next(c for c in cargos if c["id"] == cargo["id"])
    assert sigue["nombre"] == cargo["nombre"]


def test_catalogo_inexistente_devuelve_404(client, reclutador_headers):
    respuesta = client.get("/api/v1/catalogos/inventado", headers=reclutador_headers)
    assert respuesta.status_code == 404


def test_catalogo_requiere_autenticacion(client):
    assert client.get("/api/v1/catalogos/nombres-cargo").status_code == 401
