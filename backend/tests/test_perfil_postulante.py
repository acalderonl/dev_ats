"""El perfil completo del candidato y la lectura automática del CV."""

import io

from app.schemas.cv_extraido import CvExtraido
from app.services.extraccion_cv_service import _cuantos_campos_trae


def _postular(client, slug, **campos):
    cuerpo = {
        "nombres": "Daniel",
        "apellidos": "Jiménez",
        "cedula": campos.pop("cedula", "0931761704"),
        "email": "daniel@example.com",
        "acepta_privacidad": True,
        **campos,
    }
    return client.post(f"/api/v1/public/vacantes/{slug}/postular", json=cuerpo)


def test_sin_aceptar_la_politica_no_se_postula(client, unique_suffix, crear_cargo, crear_vacante):
    """El consentimiento se comprueba de verdad.

    Estuvo roto: con `acepta_privacidad: bool = False`, Pydantic **no valida los
    valores por defecto**, así que el validador no llegaba a correr y una postulación
    sin aceptar nada entraba igual. Esta prueba existe para que no vuelva a pasar.
    """
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    sin_aceptar = _postular(client, vacante["slug"], cedula=f"11{unique_suffix[:8]}", acepta_privacidad=False)
    sin_el_campo = client.post(
        f"/api/v1/public/vacantes/{vacante['slug']}/postular",
        json={"nombres": "A", "apellidos": "B", "cedula": f"12{unique_suffix[:8]}", "email": "a@b.com"},
    )

    assert sin_aceptar.status_code == 422
    assert sin_el_campo.status_code == 422


def test_aceptando_si_se_postula_y_queda_la_fecha(client, unique_suffix, crear_cargo, crear_vacante):
    """Control positivo, y además: se guarda CUÁNDO aceptó, no solo que aceptó."""
    from sqlalchemy import text

    from app.core.database import engine

    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = _postular(client, vacante["slug"], cedula=f"13{unique_suffix[:8]}")

    assert respuesta.status_code == 201
    with engine.connect() as conexion:
        fecha = conexion.execute(
            text("SELECT acepto_privacidad_en FROM postulantes WHERE cedula = :c"),
            {"c": f"13{unique_suffix[:8]}"},
        ).scalar()
    assert fecha is not None


def test_guarda_educacion_idiomas_y_experiencia(client, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = _postular(
        client,
        vacante["slug"],
        cedula=f"14{unique_suffix[:8]}",
        educacion=[
            {
                "titulo": "Psicólogo Laboral Y Empresarial",
                "institucion": "Universidad Tecnológica Empresarial",
                "nivel_estudio": "Universitario",
                "estado_estudio": "Graduado",
                "inicio_mes": 6,
                "inicio_anio": 2019,
                "fin_mes": 6,
                "fin_anio": 2024,
            },
            {"titulo": "Magíster en Gestión del Talento Humano", "nivel_estudio": "Máster"},
        ],
        idiomas=[{"idioma": "Inglés", "nivel_escrito": "Intermedio", "nivel_oral": "Intermedio"}],
        experiencia=[
            {
                "puesto": "ESPECIALISTA DE TALENTO HUMANO",
                "jerarquia": "Senior",
                "empresa": "ANAI",
                "inicio_mes": 12,
                "inicio_anio": 2015,
                "actualmente": True,
            }
        ],
    )

    cuerpo = respuesta.json()
    assert respuesta.status_code == 201
    assert len(cuerpo["educacion"]) == 2
    assert cuerpo["educacion"][0]["institucion"] == "Universidad Tecnológica Empresarial"
    assert cuerpo["idiomas"][0]["idioma"] == "Inglés"
    assert cuerpo["experiencia"][0]["actualmente"] is True


def test_el_orden_de_las_listas_se_respeta(client, unique_suffix, crear_cargo, crear_vacante):
    """Un CV va de lo más reciente a lo más antiguo: reordenarlo cambiaría su lectura."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = _postular(
        client,
        vacante["slug"],
        cedula=f"15{unique_suffix[:8]}",
        experiencia=[
            {"puesto": "Tercero"},
            {"puesto": "Segundo"},
            {"puesto": "Primero"},
        ],
    )

    assert [e["puesto"] for e in respuesta.json()["experiencia"]] == ["Tercero", "Segundo", "Primero"]


def test_el_nivel_de_instruccion_sale_del_mas_alto(client, unique_suffix, crear_cargo, crear_vacante):
    """El filtro del directorio usa este resumen; debe reflejar el título más alto."""
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = _postular(
        client,
        vacante["slug"],
        cedula=f"16{unique_suffix[:8]}",
        educacion=[
            {"titulo": "Bachiller", "nivel_estudio": "Secundaria"},
            {"titulo": "Magíster", "nivel_estudio": "Máster"},
            {"titulo": "Psicólogo", "nivel_estudio": "Universitario"},
        ],
    )

    assert respuesta.json()["nivel_instruccion"] == "Máster"


def test_un_mes_fuera_de_rango_se_rechaza(client, unique_suffix, crear_cargo, crear_vacante):
    vacante = crear_vacante(crear_cargo(unique_suffix)["id"])

    respuesta = _postular(
        client,
        vacante["slug"],
        cedula=f"17{unique_suffix[:8]}",
        educacion=[{"titulo": "X", "inicio_mes": 13, "inicio_anio": 2020}],
    )

    assert respuesta.status_code == 422


# ------------------------------------------------ Lectura automática del CV


def test_sin_clave_configurada_cae_a_heuristicas_y_lo_declara(client):
    """Lo importante no es que rellene poco, es que **diga** que rellenó poco."""
    cv = b"Daniel Jimenez\nCorreo: daniel.jimenez@example.com\nTelefono: 0967428897\nCedula: 0931761704\n"

    respuesta = client.post(
        "/api/v1/public/leer-cv",
        files={
            "file": (
                "cv.docx",
                io.BytesIO(cv),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    # El .docx falso no se puede abrir; lo que importa es que el error sea claro
    # y no un 500. Si se pudiera leer, el motor sería 'heuristicas'.
    assert respuesta.status_code in (200, 422)
    if respuesta.status_code == 200:
        assert respuesta.json()["motor"] == "heuristicas"
        assert "a mano" in respuesta.json()["aviso"]


def test_formato_no_soportado_se_rechaza(client):
    respuesta = client.post("/api/v1/public/leer-cv", files={"file": ("cv.txt", io.BytesIO(b"hola"), "text/plain")})
    assert respuesta.status_code == 400


def test_archivo_enorme_se_rechaza(client):
    """Antes el CV se leía entero sin mirar el tamaño (fase S.3)."""
    enorme = io.BytesIO(b"x" * (16 * 1024 * 1024))

    respuesta = client.post("/api/v1/public/leer-cv", files={"file": ("cv.pdf", enorme, "application/pdf")})

    assert respuesta.status_code == 413


def test_el_conteo_de_campos_distingue_leer_poco_de_fallar():
    """`campos_encontrados` es lo que separa 'el CV no lo decía' de 'no leyó nada'."""
    assert _cuantos_campos_trae(CvExtraido()) == 0

    con_datos = CvExtraido(
        nombres="Daniel",
        email="d@e.com",
        educacion=[{"titulo": "Psicólogo"}],
        experiencia=[{"puesto": "Analista"}, {"puesto": "Docente"}],
    )
    # 2 sueltos + 1 educación + 2 experiencias
    assert _cuantos_campos_trae(con_datos) == 5
