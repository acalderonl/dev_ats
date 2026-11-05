"""Departamentos: la unidad organizativa de los cargos.

Lo que se fija aquí: que un cargo tiene siempre departamento, que «Sin asignar» existe
desde la migración y no se puede tocar, y que desactivar un departamento no deja cargos
colgando en el aire.
"""


def _crear_departamento(client, headers, nombre: str):
    respuesta = client.post("/api/v1/departamentos", json={"nombre": nombre}, headers=headers)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _sin_asignar(client, headers):
    return next(d for d in client.get("/api/v1/departamentos", headers=headers).json() if d["es_sistema"])


# ----------------------------------------------------------- El de respaldo


def test_sin_asignar_existe_desde_la_migracion(client, reclutador_headers):
    """Sin él, el primer cargo no tendría a dónde ir."""
    respaldo = _sin_asignar(client, reclutador_headers)

    assert respaldo["nombre"] == "Sin asignar"
    assert respaldo["activo"] is True


def test_sin_asignar_no_se_desactiva(client, reclutador_headers):
    respaldo = _sin_asignar(client, reclutador_headers)

    respuesta = client.patch(f"/api/v1/departamentos/{respaldo['id']}/toggle-activo", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "Sin asignar" in respuesta.json()["detail"]


def test_sin_asignar_no_se_renombra(client, reclutador_headers):
    """El sistema lo busca por ese nombre."""
    respaldo = _sin_asignar(client, reclutador_headers)

    respuesta = client.put(
        f"/api/v1/departamentos/{respaldo['id']}", json={"nombre": "Otro"}, headers=reclutador_headers
    )

    assert respuesta.status_code == 400


# ------------------------------------------------------------------- CRUD


def test_crear_y_listar(client, reclutador_headers, unique_suffix):
    creado = _crear_departamento(client, reclutador_headers, f"Académico {unique_suffix}")

    nombres = [d["nombre"] for d in client.get("/api/v1/departamentos", headers=reclutador_headers).json()]

    assert creado["nombre"] == f"Académico {unique_suffix}"
    assert creado["cargos"] == 0
    assert f"Académico {unique_suffix}" in nombres


def test_el_nombre_no_se_repite_ni_cambiando_mayusculas(client, reclutador_headers, unique_suffix):
    _crear_departamento(client, reclutador_headers, f"Finanzas {unique_suffix}")

    respuesta = client.post(
        "/api/v1/departamentos", json={"nombre": f"FINANZAS {unique_suffix}"}, headers=reclutador_headers
    )

    assert respuesta.status_code == 409


def test_un_entrevistador_no_crea_departamentos(client, entrevistador_headers, unique_suffix):
    respuesta = client.post(
        "/api/v1/departamentos", json={"nombre": f"X {unique_suffix}"}, headers=entrevistador_headers
    )

    assert respuesta.status_code == 403


# ------------------------------------------------------ Relación con cargos


def test_un_cargo_lleva_su_departamento(client, reclutador_headers, unique_suffix, crear_cargo):
    departamento = _crear_departamento(client, reclutador_headers, f"Sistemas {unique_suffix}")

    cargo = crear_cargo(unique_suffix, departamento_id=departamento["id"])

    assert cargo["departamento_id"] == departamento["id"]
    assert cargo["departamento"] == f"Sistemas {unique_suffix}"


def test_el_conteo_de_cargos_sube(client, reclutador_headers, unique_suffix, crear_cargo):
    departamento = _crear_departamento(client, reclutador_headers, f"Conteo {unique_suffix}")
    crear_cargo(unique_suffix, departamento_id=departamento["id"])

    actualizado = next(
        d
        for d in client.get("/api/v1/departamentos", headers=reclutador_headers).json()
        if d["id"] == departamento["id"]
    )

    assert actualizado["cargos"] == 1


def test_un_cargo_sin_departamento_se_rechaza(client, reclutador_headers, unique_suffix):
    """Obligatorio de verdad, no solo en la pantalla."""
    nombre = client.post(
        "/api/v1/catalogos/nombres-cargo", json={"nombre": f"Sin depto {unique_suffix}"}, headers=reclutador_headers
    ).json()

    respuesta = client.post("/api/v1/cargos", json={"nombre_id": nombre["id"]}, headers=reclutador_headers)

    assert respuesta.status_code == 422


def test_un_departamento_inexistente_se_rechaza_con_mensaje(client, reclutador_headers, unique_suffix):
    nombre = client.post(
        "/api/v1/catalogos/nombres-cargo", json={"nombre": f"Depto falso {unique_suffix}"}, headers=reclutador_headers
    ).json()

    respuesta = client.post(
        "/api/v1/cargos", json={"nombre_id": nombre["id"], "departamento_id": 999999}, headers=reclutador_headers
    )

    assert respuesta.status_code == 400
    assert "no existe" in respuesta.json()["detail"]


def test_al_desactivar_sus_cargos_pasan_a_sin_asignar(client, reclutador_headers, unique_suffix, crear_cargo):
    """Lo que más importa: desactivar un departamento no deja cargos colgando.

    Se mueven de verdad, no se esconden: un cargo tiene que tener siempre un
    departamento al que pertenecer, y uno desactivado ya no cuenta como tal.
    """
    departamento = _crear_departamento(client, reclutador_headers, f"Cerrado {unique_suffix}")
    cargo = crear_cargo(unique_suffix, departamento_id=departamento["id"])
    respaldo = _sin_asignar(client, reclutador_headers)

    client.patch(f"/api/v1/departamentos/{departamento['id']}/toggle-activo", headers=reclutador_headers)

    movido = next(c for c in client.get("/api/v1/cargos", headers=reclutador_headers).json() if c["id"] == cargo["id"])
    assert movido["departamento_id"] == respaldo["id"]
    assert movido["departamento"] == "Sin asignar"


def test_un_departamento_desactivado_no_recibe_cargos(client, reclutador_headers, unique_suffix):
    departamento = _crear_departamento(client, reclutador_headers, f"Apagado {unique_suffix}")
    client.patch(f"/api/v1/departamentos/{departamento['id']}/toggle-activo", headers=reclutador_headers)
    nombre = client.post(
        "/api/v1/catalogos/nombres-cargo", json={"nombre": f"Tarde {unique_suffix}"}, headers=reclutador_headers
    ).json()

    respuesta = client.post(
        "/api/v1/cargos",
        json={"nombre_id": nombre["id"], "departamento_id": departamento["id"]},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    assert "desactivado" in respuesta.json()["detail"]
