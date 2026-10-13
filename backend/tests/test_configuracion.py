"""Configuración: quién puede verla y que los secretos no salgan nunca.

Lo importante aquí no es que guarde, es que **no devuelva** lo que guarda y que en la
base no esté en claro. Una prueba que solo comprobara "guardé y leí lo mismo" pasaría
igual con los secretos escritos en texto plano.
"""

from sqlalchemy import text

from app.core.database import engine


def _valor_crudo_en_la_base(clave: str) -> str | None:
    """Lo que hay REALMENTE en la columna, sin pasar por el servicio que descifra."""
    with engine.connect() as conexion:
        fila = conexion.execute(text("SELECT valor FROM configuracion WHERE clave = :clave"), {"clave": clave}).first()
    return fila[0] if fila else None


def test_solo_super_admin_lee_la_configuracion(client, reclutador_headers, admin_headers):
    assert client.get("/api/v1/configuracion", headers=reclutador_headers).status_code == 403
    assert client.get("/api/v1/configuracion", headers=admin_headers).status_code == 200


def test_el_secreto_no_se_guarda_en_claro(client, admin_headers):
    client.put(
        "/api/v1/configuracion",
        json={"linkedin_client_secret": "secreto-de-linkedin-12345"},
        headers=admin_headers,
    )

    crudo = _valor_crudo_en_la_base("linkedin_client_secret")

    assert crudo is not None
    assert "secreto-de-linkedin-12345" not in crudo


def test_el_secreto_no_se_devuelve_nunca(client, admin_headers):
    client.put(
        "/api/v1/configuracion",
        json={"gmail_password_app": "abcd efgh ijkl mnop"},
        headers=admin_headers,
    )

    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()

    assert cuerpo["gmail_password_app"] is None
    assert cuerpo["gmail_password_app_configurado"] is True
    assert cuerpo["gmail_password_app_pista"] == "...mnop"
    assert "abcd efgh ijkl mnop" not in str(cuerpo)


def test_guardar_otro_campo_no_borra_el_secreto(client, admin_headers):
    """La pantalla manda los secretos vacíos porque nunca los recibe.

    Si "vacío" significara "bórralo", abrir Configuración y cambiar el nombre de la
    empresa dejaría la integración muerta sin que nadie lo pidiera.
    """
    client.put(
        "/api/v1/configuracion",
        json={"linkedin_client_secret": "no-me-borres"},
        headers=admin_headers,
    )

    client.put("/api/v1/configuracion", json={"empresa_nombre": "ACME"}, headers=admin_headers)

    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()
    assert cuerpo["empresa_nombre"] == "ACME"
    assert cuerpo["linkedin_client_secret_configurado"] is True


def test_borrar_el_secreto_a_proposito_si_funciona(client, admin_headers):
    """Control negativo del anterior: mandarlo vacío EXPLÍCITAMENTE sí lo borra."""
    client.put("/api/v1/configuracion", json={"linkedin_client_secret": "algo"}, headers=admin_headers)

    client.put("/api/v1/configuracion", json={"linkedin_client_secret": ""}, headers=admin_headers)

    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()
    assert cuerpo["linkedin_client_secret_configurado"] is False


def test_conectar_linkedin_sin_credenciales_avisa(client, admin_headers):
    client.put(
        "/api/v1/configuracion",
        json={"linkedin_client_id": "", "linkedin_client_secret": "", "linkedin_redirect_uri": ""},
        headers=admin_headers,
    )

    respuesta = client.post("/api/v1/configuracion/linkedin/conectar", headers=admin_headers)

    assert respuesta.status_code == 400
    assert "configurar" in respuesta.json()["detail"].lower()


def test_estado_de_linkedin_sin_conectar(client, reclutador_headers):
    cuerpo = client.get("/api/v1/configuracion/linkedin/estado", headers=reclutador_headers).json()

    assert cuerpo["cuenta_conectada"] is False


def test_jornadas_se_leen_por_cualquiera_y_solo_admin_las_crea(client, reclutador_headers, admin_headers):
    assert client.get("/api/v1/configuracion/jornadas", headers=reclutador_headers).status_code == 200

    cuerpo = {"nombre": "Jornada de prueba", "horas": "7.5"}
    assert client.post("/api/v1/configuracion/jornadas", json=cuerpo, headers=reclutador_headers).status_code == 403

    creada = client.post("/api/v1/configuracion/jornadas", json=cuerpo, headers=admin_headers)
    assert creada.status_code == 201
    assert creada.json()["horas"] == "7.50"


def test_jornada_repetida_se_rechaza(client, admin_headers):
    cuerpo = {"nombre": "Jornada duplicada", "horas": "8"}
    assert client.post("/api/v1/configuracion/jornadas", json=cuerpo, headers=admin_headers).status_code == 201
    assert client.post("/api/v1/configuracion/jornadas", json=cuerpo, headers=admin_headers).status_code == 409


def test_jornada_de_cero_horas_se_rechaza(client, admin_headers):
    respuesta = client.post(
        "/api/v1/configuracion/jornadas", json={"nombre": "Nula", "horas": "0"}, headers=admin_headers
    )
    assert respuesta.status_code == 422
