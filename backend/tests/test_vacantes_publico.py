def test_crear_vacante_genera_slug_unico(client, unique_suffix, crear_cargo, crear_vacante):
    """Dos vacantes del mismo cargo no pueden compartir URL pública."""
    cargo_id = crear_cargo(unique_suffix)["id"]

    primera = crear_vacante(cargo_id)
    segunda = crear_vacante(cargo_id)

    assert primera["slug"] != segunda["slug"]


def test_el_titulo_se_copia_del_cargo(client, unique_suffix, crear_cargo, crear_vacante):
    """El título ya no se escribe: sale del cargo, y lo que mande el cliente se ignora."""
    cargo = crear_cargo(unique_suffix)

    vacante = crear_vacante(cargo["id"], titulo="Título inventado por el cliente")

    assert vacante["titulo"] == cargo["nombre"]
    assert "inventado" not in vacante["slug"]


def test_vacante_abierta_es_visible_publicamente(client, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id)

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")

    assert response.status_code == 200
    assert response.json()["titulo"] == vacante["titulo"]


def test_vacante_en_borrador_no_es_visible(client, unique_suffix, crear_cargo, crear_vacante):
    """Un borrador no se publica aunque alguien tenga el enlace."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id, estado="borrador")

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")

    assert response.status_code == 410


def test_vacante_interna_no_aparece_en_el_portal(client, unique_suffix, crear_cargo, crear_vacante):
    """Interna significa interna: abierta, vigente, y aun así invisible fuera."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(
        cargo_id,
        visibilidad="interna",
        destinatarios_internos=["persona@empresa.com"],
    )

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")

    assert response.status_code == 404


def test_vacante_mixta_si_aparece_en_el_portal(client, unique_suffix, crear_cargo, crear_vacante):
    """Control positivo de la anterior: mixta sale fuera además de dentro."""
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(
        cargo_id,
        visibilidad="mixta",
        destinatarios_internos=["persona@empresa.com"],
    )

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")

    assert response.status_code == 200


def test_vacante_expirada_devuelve_410(client, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id, dias_de_plazo=-1)

    response = client.get(f"/api/v1/public/vacantes/{vacante['slug']}")

    assert response.status_code == 410


def test_postular_a_vacante_expirada_devuelve_410(client, unique_suffix, crear_cargo, crear_vacante):
    cargo_id = crear_cargo(unique_suffix)["id"]
    vacante = crear_vacante(cargo_id, dias_de_plazo=-1)

    response = client.post(
        f"/api/v1/public/vacantes/{vacante['slug']}/postular",
        json={
            "nombres": "Juan",
            "apellidos": "Pérez",
            "cedula": f"17{unique_suffix[:8]}",
            "email": "juan.perez@example.com",
            "acepta_privacidad": True,
        },
    )

    assert response.status_code == 410
