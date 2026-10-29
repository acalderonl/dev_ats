"""El nombre del campo con el que se suben los archivos.

FastAPI busca el campo del formulario por **el nombre del parámetro**, y el frontend
manda siempre `file` (`apiUpload` en `lib/apiClient.ts`). Un parámetro llamado de otra
forma no da un error claro: da un 422 que parece culpa del archivo.

Pasó de verdad: `POST /vacantes/imagen` tenía el parámetro `archivo`, así que subir la
imagen del post devolvía 422 **siempre**. No lo cazó nadie porque esa ruta no tenía
prueba, y las que sí la tienen las escribió quien también escribió el endpoint, usando
su mismo nombre. Por eso la segunda prueba de aquí no mira una ruta: las mira todas.
"""

UN_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_la_imagen_del_post_se_sube_con_el_campo_file(client, reclutador_headers, tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "media_root", str(tmp_path))

    respuesta = client.post(
        "/api/v1/vacantes/imagen",
        files={"file": ("post.png", UN_PNG, "image/png")},
        headers=reclutador_headers,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["url"].endswith(".png")


def test_todas_las_rutas_de_subida_usan_el_mismo_campo(client):
    """Ninguna ruta que reciba un archivo puede llamar al campo de otra manera.

    Se lee del esquema de la propia aplicación, así que cubre también las rutas que
    aún no existen cuando se escribe esto.
    """
    esquema = client.get("/openapi.json").json()
    MULTIPART = "multipart/form-data"

    discrepantes = []
    for ruta, metodos in esquema["paths"].items():
        for metodo, definicion in metodos.items():
            cuerpo = definicion.get("requestBody", {}).get("content", {}).get(MULTIPART)
            if not cuerpo:
                continue
            referencia = cuerpo["schema"].get("$ref", "").rsplit("/", 1)[-1]
            propiedades = esquema["components"]["schemas"][referencia]["properties"]
            if list(propiedades) != ["file"]:
                discrepantes.append(f"{metodo.upper()} {ruta} -> {list(propiedades)}")

    assert not discrepantes, "Estas rutas devolverán 422 al frontend: " + "; ".join(discrepantes)
