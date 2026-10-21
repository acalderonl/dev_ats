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


# --------------------------------------------------------- Conexión de correo


def test_sin_elegir_tipo_se_asume_gmail(client, admin_headers):
    """Lo que había antes era Gmail: no cambiar de conexión a quien ya lo tenía puesto."""
    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()
    assert cuerpo["correo_tipo"] in (None, "gmail")


def test_tipo_de_correo_invalido_se_rechaza(client, admin_headers):
    respuesta = client.put("/api/v1/configuracion", json={"correo_tipo": "paloma_mensajera"}, headers=admin_headers)
    assert respuesta.status_code == 422


def test_cifrado_smtp_invalido_se_rechaza(client, admin_headers):
    respuesta = client.put("/api/v1/configuracion", json={"smtp_cifrado": "rot13"}, headers=admin_headers)
    assert respuesta.status_code == 422


def test_puerto_smtp_debe_ser_numero_en_rango(client, admin_headers):
    assert (
        client.put("/api/v1/configuracion", json={"smtp_puerto": "quinientos"}, headers=admin_headers).status_code
        == 422
    )
    assert client.put("/api/v1/configuracion", json={"smtp_puerto": "99999"}, headers=admin_headers).status_code == 422
    assert client.put("/api/v1/configuracion", json={"smtp_puerto": "587"}, headers=admin_headers).status_code == 200


def test_la_contrasena_smtp_tampoco_se_guarda_en_claro(client, admin_headers):
    client.put(
        "/api/v1/configuracion", json={"smtp_password": "clave-del-servidor-institucional"}, headers=admin_headers
    )

    crudo = _valor_crudo_en_la_base("smtp_password")

    assert crudo is not None
    assert "clave-del-servidor-institucional" not in crudo


def test_la_contrasena_smtp_no_se_devuelve(client, admin_headers):
    client.put("/api/v1/configuracion", json={"smtp_password": "abcdefgh1234"}, headers=admin_headers)

    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()

    assert cuerpo["smtp_password"] is None
    assert cuerpo["smtp_password_configurado"] is True
    assert cuerpo["smtp_password_pista"] == "...1234"


def test_cambiar_de_tipo_no_borra_las_credenciales_del_otro(client, admin_headers):
    """Probar el servidor propio y volver a Gmail no puede costar reconfigurar Gmail."""
    client.put(
        "/api/v1/configuracion",
        json={"correo_tipo": "gmail", "gmail_remitente": "rrhh@empresa.com", "gmail_password_app": "wxyz"},
        headers=admin_headers,
    )

    client.put(
        "/api/v1/configuracion",
        json={"correo_tipo": "smtp", "smtp_servidor": "mail.empresa.com", "smtp_password": "otra"},
        headers=admin_headers,
    )

    cuerpo = client.get("/api/v1/configuracion", headers=admin_headers).json()
    assert cuerpo["correo_tipo"] == "smtp"
    assert cuerpo["gmail_remitente"] == "rrhh@empresa.com"
    assert cuerpo["gmail_password_app_configurado"] is True
    assert cuerpo["smtp_password_configurado"] is True


def test_probar_correo_sin_configurar_dice_que_falta(client, admin_headers):
    """Devuelve 200 con ok=false: que falte configuración es una respuesta, no un error."""
    client.put(
        "/api/v1/configuracion",
        json={"correo_tipo": "smtp", "smtp_servidor": "", "smtp_puerto": "", "smtp_password": ""},
        headers=admin_headers,
    )

    respuesta = client.post("/api/v1/configuracion/correo/probar", headers=admin_headers)

    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is False
    assert "SMTP" in respuesta.json()["mensaje"]


def test_probar_correo_es_solo_de_super_admin(client, reclutador_headers):
    assert client.post("/api/v1/configuracion/correo/probar", headers=reclutador_headers).status_code == 403


# --------------------------------------------------------- Conexión con LinkedIn


def _credenciales_de_linkedin(client, admin_headers):
    client.put(
        "/api/v1/configuracion",
        json={
            "linkedin_client_id": "id-de-prueba",
            "linkedin_client_secret": "secreto-de-prueba",
            "linkedin_redirect_uri": "http://localhost:3000/configuracion/linkedin",
        },
        headers=admin_headers,
    )


def test_conectar_devuelve_url_con_los_parametros_de_oauth(client, admin_headers):
    _credenciales_de_linkedin(client, admin_headers)

    cuerpo = client.post("/api/v1/configuracion/linkedin/conectar", headers=admin_headers).json()

    assert cuerpo["url"].startswith("https://www.linkedin.com/oauth/v2/authorization")
    assert "client_id=id-de-prueba" in cuerpo["url"]
    # La redirect uri va codificada: sin eso, LinkedIn la corta en los dos puntos.
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fconfiguracion%2Flinkedin" in cuerpo["url"]
    assert "w_member_social" in cuerpo["url"]
    assert cuerpo["state"]


def test_el_state_de_otra_persona_se_rechaza(client, admin_headers, reclutador_headers):
    """Sin esto, alguien podría enganchar SU cuenta de LinkedIn a la sesión de otro."""
    _credenciales_de_linkedin(client, admin_headers)
    state_del_reclutador = client.post("/api/v1/configuracion/linkedin/conectar", headers=reclutador_headers).json()[
        "state"
    ]

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/callback",
        json={"code": "lo-que-sea", "state": state_del_reclutador},
        headers=admin_headers,
    )

    assert respuesta.status_code == 400
    assert "otra sesión" in respuesta.json()["detail"]


def test_un_state_inventado_se_rechaza(client, admin_headers):
    _credenciales_de_linkedin(client, admin_headers)

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/callback",
        json={"code": "lo-que-sea", "state": "esto-no-lo-firmamos-nosotros"},
        headers=admin_headers,
    )

    assert respuesta.status_code == 400


def test_el_state_propio_pasa_la_comprobacion(client, admin_headers):
    """Control positivo: el state válido llega a canjear el código.

    Falla después, al salir a LinkedIn con un código inventado, y eso es lo correcto:
    demuestra que la comprobación de `state` no es la que bloquea.
    """
    _credenciales_de_linkedin(client, admin_headers)
    propio = client.post("/api/v1/configuracion/linkedin/conectar", headers=admin_headers).json()["state"]

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/callback",
        json={"code": "codigo-inventado", "state": propio},
        headers=admin_headers,
    )

    assert respuesta.status_code == 502
    assert "LinkedIn" in respuesta.json()["detail"]


def test_el_state_caducado_se_rechaza(client, admin_headers):
    from datetime import datetime, timedelta, timezone

    from jose import jwt

    from app.core.config import get_settings

    ajustes = get_settings()
    caducado = jwt.encode(
        {
            "sub": "da-igual",
            "typ": "linkedin_oauth",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        ajustes.secret_key,
        algorithm=ajustes.algorithm,
    )

    respuesta = client.post(
        "/api/v1/configuracion/linkedin/callback",
        json={"code": "x", "state": caducado},
        headers=admin_headers,
    )

    assert respuesta.status_code == 400
    assert "caduc" in respuesta.json()["detail"]
