"""Usuarios, roles y permisos.

Lo que más importa aquí no es que el CRUD guarde, sino que **no se pueda dejar el
sistema sin administrador**: las tres formas de quedarse fuera tienen su prueba.
"""

import uuid


def _nuevo_usuario(sufijo: str, **campos) -> dict:
    return {
        "email": f"nuevo.{sufijo}@empresa.com",
        "nombres": "Nuevo",
        "apellidos": "Usuario",
        "password": "ClaveLarga2026",
        "rol": "reclutador",
        **campos,
    }


# ------------------------------------------------------------- CRUD de usuarios


def test_crear_editar_y_desactivar_usuario(client, admin_headers, unique_suffix):
    creado = client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix), headers=admin_headers)
    assert creado.status_code == 201, creado.text
    usuario = creado.json()
    assert usuario["rol"] == "reclutador"
    assert usuario["activo"] is True

    editado = client.put(
        f"/api/v1/users/{usuario['id']}",
        json={"nombres": "Nombre Cambiado", "rol": "entrevistador"},
        headers=admin_headers,
    )
    assert editado.status_code == 200
    assert editado.json()["nombres"] == "Nombre Cambiado"
    assert editado.json()["rol"] == "entrevistador"

    desactivado = client.patch(f"/api/v1/users/{usuario['id']}/activo", json={"activo": False}, headers=admin_headers)
    assert desactivado.status_code == 200
    assert desactivado.json()["activo"] is False


def test_el_correo_repetido_se_rechaza(client, admin_headers, unique_suffix):
    cuerpo = _nuevo_usuario(unique_suffix)
    assert client.post("/api/v1/users", json=cuerpo, headers=admin_headers).status_code == 201

    repetido = client.post("/api/v1/users", json=cuerpo, headers=admin_headers)

    assert repetido.status_code == 409
    assert "Ya existe" in repetido.json()["detail"]


def test_la_clave_corta_se_rechaza(client, admin_headers, unique_suffix):
    respuesta = client.post(
        "/api/v1/users", json=_nuevo_usuario(unique_suffix, password="corta"), headers=admin_headers
    )
    assert respuesta.status_code == 422


def test_un_rol_inexistente_se_rechaza(client, admin_headers, unique_suffix):
    respuesta = client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix, rol="inventado"), headers=admin_headers)
    assert respuesta.status_code == 400
    assert "no existe" in respuesta.json()["detail"]


def test_restablecer_la_clave_permite_entrar_con_la_nueva(client, admin_headers, unique_suffix):
    """Control positivo de verdad: la clave nueva sirve para iniciar sesión."""
    usuario = client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix), headers=admin_headers).json()

    cambio = client.put(
        f"/api/v1/users/{usuario['id']}/password",
        json={"password": "OtraClaveLarga2026"},
        headers=admin_headers,
    )
    assert cambio.status_code == 204

    entrada = client.post("/api/v1/auth/login", json={"email": usuario["email"], "password": "OtraClaveLarga2026"})
    assert entrada.status_code == 200


# ------------------------------------- No quedarse fuera del propio sistema


def test_no_puedo_desactivarme_a_mi_mismo(client, admin_headers):
    yo = client.get("/api/v1/users", headers=admin_headers).json()
    admin = next(u for u in yo if u["email"] == "admin@atsdemo.com")

    respuesta = client.patch(f"/api/v1/users/{admin['id']}/activo", json={"activo": False}, headers=admin_headers)

    assert respuesta.status_code == 400
    assert "a ti mismo" in respuesta.json()["detail"]


def test_no_puedo_quitarme_mi_propio_super_admin(client, admin_headers):
    usuarios = client.get("/api/v1/users", headers=admin_headers).json()
    admin = next(u for u in usuarios if u["email"] == "admin@atsdemo.com")

    respuesta = client.put(f"/api/v1/users/{admin['id']}", json={"rol": "reclutador"}, headers=admin_headers)

    assert respuesta.status_code == 400
    assert "super admin" in respuesta.json()["detail"]


def test_no_se_puede_dejar_el_sistema_sin_super_admin(client, admin_headers, unique_suffix):
    """El último super admin activo no se puede degradar ni apagar.

    Se prueba con OTRO super admin para no chocar con la regla de "a ti mismo": lo que
    se comprueba aquí es la cuenta de super admins restantes, no quién pulsa.
    """
    otro = client.post(
        "/api/v1/users", json=_nuevo_usuario(unique_suffix, rol="super_admin"), headers=admin_headers
    ).json()

    # Con dos super admins, degradar al otro sí se puede.
    assert (
        client.put(f"/api/v1/users/{otro['id']}", json={"rol": "reclutador"}, headers=admin_headers).status_code == 200
    )

    # Y ahora que solo queda uno (el que pulsa), no puede degradarse: lo impide la
    # regla de "a ti mismo", que es la que aplica primero.
    usuarios = client.get("/api/v1/users", headers=admin_headers).json()
    admin = next(u for u in usuarios if u["email"] == "admin@atsdemo.com")
    assert (
        client.put(f"/api/v1/users/{admin['id']}", json={"rol": "reclutador"}, headers=admin_headers).status_code == 400
    )


# ----------------------------------------------------------------- CRUD de roles


def test_crear_rol_con_permisos_y_asignarlo(client, admin_headers, unique_suffix):
    nombre = f"coordinador_{unique_suffix[:6]}"

    creado = client.post(
        "/api/v1/roles",
        json={
            "nombre": nombre,
            "descripcion": "Ve vacantes y evalúa",
            "permisos": ["dashboard.ver", "vacantes.ver", "evaluaciones.ver", "evaluaciones.crear"],
        },
        headers=admin_headers,
    )

    assert creado.status_code == 201, creado.text
    assert creado.json()["es_sistema"] is False
    assert sorted(creado.json()["permisos"]) == [
        "dashboard.ver",
        "evaluaciones.crear",
        "evaluaciones.ver",
        "vacantes.ver",
    ]

    usuario = client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix, rol=nombre), headers=admin_headers)
    assert usuario.status_code == 201
    assert usuario.json()["rol"] == nombre


def test_el_nombre_del_rol_se_normaliza(client, admin_headers, unique_suffix):
    """'Jefe De Area' se guarda como 'jefe_de_area': se usa como identificador."""
    creado = client.post(
        "/api/v1/roles",
        json={"nombre": f"Jefe De Area {unique_suffix[:4]}".replace(" ", " "), "permisos": []},
        headers=admin_headers,
    )
    assert creado.status_code == 201
    assert " " not in creado.json()["nombre"]
    assert creado.json()["nombre"] == creado.json()["nombre"].lower()


def test_un_permiso_inventado_se_rechaza(client, admin_headers, unique_suffix):
    respuesta = client.post(
        "/api/v1/roles",
        json={"nombre": f"rol_{unique_suffix[:6]}", "permisos": ["vacantes.teletransportar"]},
        headers=admin_headers,
    )
    assert respuesta.status_code == 400
    assert "desconocidos" in respuesta.json()["detail"]


def test_los_roles_del_sistema_no_se_renombran_ni_se_borran(client, admin_headers):
    """El código todavía nombra estos roles: renombrarlos rompería endpoints en silencio."""
    roles = client.get("/api/v1/roles", headers=admin_headers).json()
    reclutador = next(r for r in roles if r["nombre"] == "reclutador")

    renombrar = client.put(f"/api/v1/roles/{reclutador['id']}", json={"nombre": "otro_nombre"}, headers=admin_headers)
    borrar = client.delete(f"/api/v1/roles/{reclutador['id']}", headers=admin_headers)

    assert renombrar.status_code == 400
    assert "del sistema" in renombrar.json()["detail"]
    assert borrar.status_code == 400


def test_la_descripcion_de_un_rol_de_sistema_si_se_cambia(client, admin_headers):
    """Control positivo: protegido no quiere decir congelado."""
    roles = client.get("/api/v1/roles", headers=admin_headers).json()
    reclutador = next(r for r in roles if r["nombre"] == "reclutador")

    respuesta = client.put(
        f"/api/v1/roles/{reclutador['id']}",
        json={"descripcion": "Publica vacantes y mueve candidatos"},
        headers=admin_headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["descripcion"] == "Publica vacantes y mueve candidatos"


def test_no_se_borra_un_rol_con_usuarios(client, admin_headers, unique_suffix):
    nombre = f"temporal_{unique_suffix[:6]}"
    rol = client.post("/api/v1/roles", json={"nombre": nombre, "permisos": []}, headers=admin_headers).json()
    client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix, rol=nombre), headers=admin_headers)

    respuesta = client.delete(f"/api/v1/roles/{rol['id']}", headers=admin_headers)

    assert respuesta.status_code == 400
    assert "usuario(s)" in respuesta.json()["detail"]


def test_un_rol_sin_usuarios_si_se_borra(client, admin_headers, unique_suffix):
    """Control positivo del anterior."""
    rol = client.post(
        "/api/v1/roles", json={"nombre": f"vacio_{unique_suffix[:6]}", "permisos": []}, headers=admin_headers
    ).json()

    assert client.delete(f"/api/v1/roles/{rol['id']}", headers=admin_headers).status_code == 204


# -------------------------------------------------------------------- Permisos


def test_el_super_admin_tiene_todos_los_permisos(client, admin_headers):
    catalogo = client.get("/api/v1/roles/permisos", headers=admin_headers).json()
    mios = client.get("/api/v1/users/yo/permisos", headers=admin_headers).json()

    assert len(catalogo) > 0
    assert sorted(mios) == sorted(p["clave"] for p in catalogo)


def test_el_reclutador_no_administra_usuarios(client, reclutador_headers):
    assert client.get("/api/v1/users", headers=reclutador_headers).status_code == 403
    assert (
        client.post("/api/v1/roles", json={"nombre": "x_rol", "permisos": []}, headers=reclutador_headers).status_code
        == 403
    )


def test_un_ajuste_por_usuario_quita_un_permiso_de_su_rol(client, admin_headers, unique_suffix):
    """El caso que motiva tener dos niveles: recortar a una persona sin cambiarle el rol."""
    usuario = client.post("/api/v1/users", json=_nuevo_usuario(unique_suffix), headers=admin_headers).json()

    antes = client.get(f"/api/v1/users/{usuario['id']}/permisos", headers=admin_headers).json()
    assert "vacantes.publicar" in antes["efectivos"]

    client.put(
        f"/api/v1/users/{usuario['id']}/permisos",
        json=[{"clave": "vacantes.publicar", "concedido": False}],
        headers=admin_headers,
    )

    despues = client.get(f"/api/v1/users/{usuario['id']}/permisos", headers=admin_headers).json()
    assert "vacantes.publicar" not in despues["efectivos"]
    # El rol no se tocó: la plantilla sigue trayéndolo.
    assert "vacantes.publicar" in despues["del_rol"]


def test_un_ajuste_por_usuario_suma_un_permiso_que_el_rol_no_da(client, admin_headers, unique_suffix):
    """Control positivo del anterior, en el otro sentido."""
    usuario = client.post(
        "/api/v1/users", json=_nuevo_usuario(unique_suffix, rol="entrevistador"), headers=admin_headers
    ).json()

    antes = client.get(f"/api/v1/users/{usuario['id']}/permisos", headers=admin_headers).json()
    assert "cargos.crear" not in antes["efectivos"]

    client.put(
        f"/api/v1/users/{usuario['id']}/permisos",
        json=[{"clave": "cargos.crear", "concedido": True}],
        headers=admin_headers,
    )

    despues = client.get(f"/api/v1/users/{usuario['id']}/permisos", headers=admin_headers).json()
    assert "cargos.crear" in despues["efectivos"]


def test_al_super_admin_no_se_le_recortan_permisos(client, admin_headers, unique_suffix):
    """Si se pudiera, alguien podría dejarse fuera de su propio sistema."""
    otro = client.post(
        "/api/v1/users", json=_nuevo_usuario(unique_suffix, rol="super_admin"), headers=admin_headers
    ).json()

    respuesta = client.put(
        f"/api/v1/users/{otro['id']}/permisos",
        json=[{"clave": "usuarios.asignar_rol", "concedido": False}],
        headers=admin_headers,
    )

    assert respuesta.status_code == 400
    assert "todos los permisos" in respuesta.json()["detail"]


def test_un_usuario_inexistente_da_404(client, admin_headers):
    respuesta = client.get(f"/api/v1/users/{uuid.uuid4()}/permisos", headers=admin_headers)
    assert respuesta.status_code == 404
