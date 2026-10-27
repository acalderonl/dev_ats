"""Compartir una vacante en LinkedIn sin OAuth.

La idea: el sistema arma el contenido y abre el compositor de LinkedIn; quien publica
es la persona. Lo que hay que proteger es que LinkedIn pueda leer la tarjeta —para eso
está la página con Open Graph— y que no se comparta lo que no debe salir.
"""


def _vacante_compartible(crear_cargo, crear_vacante, sufijo, **campos):
    return crear_vacante(crear_cargo(sufijo)["id"], estado="abierta", **campos)


# ------------------------------------------- La página que lee el rastreador


def test_la_pagina_trae_las_etiquetas_con_los_datos_de_la_vacante(client, unique_suffix, crear_cargo, crear_vacante):
    """Sin esto LinkedIn arma la tarjeta con el título genérico del sitio.

    La aplicación es una SPA: al rastreador, que no ejecuta JavaScript, le llega un
    `<div id="root">` vacío. Por eso esta página la genera el servidor.
    """
    vacante = _vacante_compartible(
        crear_cargo, crear_vacante, unique_suffix, asunto="Buscamos analista", remuneracion="1200.00"
    )

    html = client.get(f"/compartir/{vacante['slug']}").text

    assert 'property="og:title"' in html
    assert "Buscamos analista" in html
    assert 'property="og:description"' in html
    # El enlace canónico lleva al formulario de verdad, no a esta página puente.
    assert f"/postular/{vacante['slug']}" in html


def test_una_persona_acaba_en_el_formulario(client, unique_suffix, crear_cargo, crear_vacante):
    """La página es para el rastreador, pero quien la abra no debe quedarse ahí."""
    vacante = _vacante_compartible(crear_cargo, crear_vacante, unique_suffix)

    html = client.get(f"/compartir/{vacante['slug']}").text

    assert 'http-equiv="refresh"' in html
    assert "location.replace" in html


def test_sin_imagen_propia_no_se_anuncia_ninguna(client, unique_suffix, crear_cargo, crear_vacante):
    """El escudo es un SVG y LinkedIn no los dibuja: saldría un hueco en la tarjeta."""
    vacante = _vacante_compartible(crear_cargo, crear_vacante, unique_suffix)

    html = client.get(f"/compartir/{vacante['slug']}").text

    assert 'property="og:image"' not in html
    assert 'name="twitter:card" content="summary"' in html


def test_con_imagen_propia_si_se_anuncia(client, unique_suffix, crear_cargo, crear_vacante):
    """Control positivo del anterior."""
    vacante = _vacante_compartible(
        crear_cargo, crear_vacante, unique_suffix, post_imagen_url="/api/v1/media/posts/x.png"
    )

    html = client.get(f"/compartir/{vacante['slug']}").text

    assert 'property="og:image"' in html
    assert "summary_large_image" in html


def test_el_titulo_con_comillas_no_rompe_la_etiqueta(client, unique_suffix, crear_cargo, crear_vacante):
    """El asunto lo escribe una persona: sin escapar, unas comillas parten el atributo."""
    vacante = _vacante_compartible(crear_cargo, crear_vacante, unique_suffix, asunto='Analista "senior" <urgente>')

    html = client.get(f"/compartir/{vacante['slug']}").text

    assert "<urgente>" not in html
    assert "&lt;urgente&gt;" in html


def test_un_borrador_no_se_comparte(client, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="borrador")

    assert client.get(f"/compartir/{vacante['slug']}").status_code == 404


def test_una_vacante_interna_no_se_comparte(client, unique_suffix, crear_cargo, crear_vacante):
    """Interna significa interna, también para el rastreador de LinkedIn."""
    vacante = crear_vacante(
        crear_cargo(unique_suffix)["id"],
        estado="abierta",
        visibilidad="interna",
        destinatarios_internos=["alguien@empresa.com"],
    )

    assert client.get(f"/compartir/{vacante['slug']}").status_code == 404


def test_una_vacante_vencida_no_se_comparte(client, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="abierta", dias_de_plazo=-1)

    assert client.get(f"/compartir/{vacante['slug']}").status_code == 404


# -------------------------------------------------- Preparar la publicación


def test_devuelve_el_texto_y_el_compositor(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    vacante = _vacante_compartible(
        crear_cargo, crear_vacante, unique_suffix, asunto="Buscamos analista", remuneracion="900.00"
    )

    cuerpo = client.post(f"/api/v1/vacantes/{vacante['id']}/compartir-linkedin", headers=reclutador_headers).json()

    assert "Buscamos analista" in cuerpo["texto"]
    assert "900.00" in cuerpo["texto"]
    assert cuerpo["url_del_compositor"].startswith("https://www.linkedin.com/sharing/share-offsite/")
    # El enlace que recibe LinkedIn es el de la página con Open Graph, no el del
    # formulario: dándole el del formulario, la tarjeta saldría vacía.
    assert "%2Fcompartir%2F" in cuerpo["url_del_compositor"]


def test_queda_como_compartido_y_no_como_publicado(
    client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante
):
    """Lo que más importa de todo esto.

    El sistema entrega el contenido, pero quien pulsa Publicar es la persona y eso no
    se puede comprobar. Marcarlo como "publicado" sería afirmar algo que no se sabe.
    """
    vacante = _vacante_compartible(crear_cargo, crear_vacante, unique_suffix)

    client.post(f"/api/v1/vacantes/{vacante['id']}/compartir-linkedin", headers=reclutador_headers)

    actualizada = next(
        v for v in client.get("/api/v1/vacantes", headers=reclutador_headers).json() if v["id"] == vacante["id"]
    )
    assert actualizada["post_estado"] == "compartido"


def test_una_vacante_interna_no_se_prepara(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(
        crear_cargo(unique_suffix)["id"],
        estado="abierta",
        visibilidad="interna",
        destinatarios_internos=["alguien@empresa.com"],
    )

    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/compartir-linkedin", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "interna" in respuesta.json()["detail"]


def test_un_borrador_no_se_prepara(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    """Si se pudiera, LinkedIn mostraría una tarjeta que lleva a un 404."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"], estado="borrador")

    respuesta = client.post(f"/api/v1/vacantes/{vacante['id']}/compartir-linkedin", headers=reclutador_headers)

    assert respuesta.status_code == 400
    assert "abierta" in respuesta.json()["detail"]
