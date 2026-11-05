"""Convocatorias: una vacante se convoca varias veces y cada vez queda registrada.

Lo que se fija aquí: que la vacante nace con su convocatoria 1, que volver a convocar
numera la 2 y cierra la anterior, que la misma persona puede postularse a cada ronda
una vez y no dos a la misma, y que el ciclo se edita por la convocatoria y no por la
vacante.
"""

from datetime import datetime, timedelta, timezone


def _en_dias(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()


def _postular(client, slug: str, cedula: str):
    return client.post(
        f"/api/v1/public/vacantes/{slug}/postular",
        json={
            "nombres": "Ana",
            "apellidos": "Prueba",
            "cedula": cedula,
            "email": f"{cedula}@example.com",
            "acepta_privacidad": True,
        },
    )


# ------------------------------------------------------- Nace con la primera


def test_la_vacante_nace_con_su_convocatoria_1(client, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], asunto="Primera ronda")

    assert len(vacante["convocatorias"]) == 1
    assert vacante["convocatoria_actual"]["numero"] == 1
    assert vacante["convocatoria_actual"]["asunto"] == "Primera ronda"
    assert vacante["convocatoria_actual"]["slug"]


def test_sin_primera_convocatoria_no_se_crea(client, reclutador_headers, unique_suffix, crear_cargo):
    """«Nueva vacante» sigue siendo un paso: siempre trae su ciclo."""
    respuesta = client.post(
        "/api/v1/vacantes",
        json={"cargo_id": crear_cargo(unique_suffix)["id"], "descripcion": "x"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 422
    assert "primera_convocatoria" in respuesta.json()["detail"]


# -------------------------------------------------------- Volver a convocar


def test_volver_a_convocar_numera_la_2_y_cierra_la_anterior(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")

    nueva = client.post(
        f"/api/v1/vacantes/{vacante['id']}/convocatorias",
        json={"fecha_limite": _en_dias(30), "estado": "abierta"},
        headers=reclutador_headers,
    )

    assert nueva.status_code == 201, nueva.text
    assert nueva.json()["numero"] == 2
    assert nueva.json()["slug"] != vacante["slug"], "cada ronda tiene su propio enlace"

    actualizada = next(
        v for v in client.get("/api/v1/vacantes", headers=reclutador_headers).json() if v["id"] == vacante["id"]
    )
    por_numero = {c["numero"]: c for c in actualizada["convocatorias"]}
    assert por_numero[1]["estado"] == "cerrada", "dos rondas abiertas a la vez serían dos enlaces para lo mismo"
    assert por_numero[2]["estado"] == "abierta"
    assert actualizada["convocatoria_actual"]["numero"] == 2


def test_la_nueva_hereda_el_post_de_la_anterior(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """«Con los mismos datos que ya se crearon»: el post no se vuelve a escribir."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], asunto="Se busca analista", post_cuerpo="Texto del post")

    nueva = client.post(
        f"/api/v1/vacantes/{vacante['id']}/convocatorias",
        json={"fecha_limite": _en_dias(30)},
        headers=reclutador_headers,
    ).json()

    assert nueva["asunto"] == "Se busca analista"
    assert nueva["post_cuerpo"] == "Texto del post"
    # Pero el ciclo empieza de cero: no hereda que la anterior ya se publicó.
    assert nueva["post_estado"] == "borrador"
    assert nueva["linkedin_post_id"] is None


def test_una_vacante_inactiva_no_se_convoca(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])
    client.patch(f"/api/v1/vacantes/{vacante['id']}/toggle-activa", headers=reclutador_headers)

    respuesta = client.post(
        f"/api/v1/vacantes/{vacante['id']}/convocatorias",
        json={"fecha_limite": _en_dias(30)},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 400
    assert "desactivada" in respuesta.json()["detail"]


# ------------------------------------------------------- Los postulantes


def test_la_misma_persona_una_vez_por_convocatoria(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    """Decisión del dueño: quien no quedó en una ronda puede intentarlo en la siguiente."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    cedula = f"77{unique_suffix[:8]}"

    assert _postular(client, vacante["slug"], cedula).status_code == 201
    repetida = _postular(client, vacante["slug"], cedula)
    assert repetida.status_code == 409
    assert "Ya te postulaste" in repetida.json()["detail"]

    segunda = client.post(
        f"/api/v1/vacantes/{vacante['id']}/convocatorias",
        json={"fecha_limite": _en_dias(30), "estado": "abierta"},
        headers=reclutador_headers,
    ).json()
    assert _postular(client, segunda["slug"], cedula).status_code == 201


def test_las_postulaciones_cuelgan_de_su_ronda(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """El pipeline sabe a qué convocatoria llegó cada persona."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    _postular(client, vacante["slug"], f"88{unique_suffix[:8]}")

    postulaciones = client.get(f"/api/v1/postulaciones?vacante_id={vacante['id']}", headers=reclutador_headers).json()

    assert len(postulaciones) == 1
    assert postulaciones[0]["convocatoria_id"] == vacante["convocatoria_id"]
    assert postulaciones[0]["convocatoria_numero"] == 1
    assert postulaciones[0]["vacante_id"] == vacante["id"]


def test_el_enlace_cerrado_deja_de_recibir(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """Al reconvocar, el enlace de la ronda anterior se apaga: no entra gente a una ronda cerrada."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta")
    client.post(
        f"/api/v1/vacantes/{vacante['id']}/convocatorias",
        json={"fecha_limite": _en_dias(30), "estado": "abierta"},
        headers=reclutador_headers,
    )

    assert client.get(f"/api/v1/public/vacantes/{vacante['slug']}").status_code == 410


# ------------------------------------------------- El ciclo va por la ronda


def test_editar_la_vacante_no_toca_el_ciclo(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """`primera_convocatoria` se ignora al editar: la fecha y el estado van por `/convocatorias`."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta", asunto="Original")

    client.put(
        f"/api/v1/vacantes/{vacante['id']}",
        json={
            "cargo_id": vacante["cargo_id"],
            "descripcion": "Cambiada",
            "primera_convocatoria": {"fecha_limite": _en_dias(99), "estado": "cerrada", "asunto": "Otra"},
        },
        headers=reclutador_headers,
    )

    actual = next(
        v for v in client.get("/api/v1/vacantes", headers=reclutador_headers).json() if v["id"] == vacante["id"]
    )["convocatoria_actual"]
    assert actual["estado"] == "abierta"
    assert actual["asunto"] == "Original"


def test_el_ciclo_se_edita_por_la_convocatoria(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = client.put(
        f"/api/v1/convocatorias/{vacante['convocatoria_id']}",
        json={"fecha_limite": _en_dias(45), "estado": "abierta", "asunto": "Editado"},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["asunto"] == "Editado"
    assert respuesta.json()["estado"] == "abierta"
    assert respuesta.json()["slug"] == vacante["slug"], "el slug no se recalcula: ya está repartido"
