"""Guardado de las imágenes del post en el volumen del contenedor.

Es la primera subida real de archivos del proyecto: hasta ahora el CV se analizaba en
memoria y se tiraba. El destino es un volumen de Docker (`media_data`), así que
sobrevive a `docker compose down` pero no a `down -v`.

Tres cosas que se comprueban antes de escribir, y por qué:

- **El tipo real, no la extensión.** Un `.png` puede ser cualquier cosa; se leen los
  primeros bytes y se compara con las firmas conocidas. La extensión la elige el
  servidor a partir de esa firma, nunca el cliente.
- **El tamaño, leyendo a trozos.** Mirar `content-length` es fiarse del cliente.
- **El nombre.** El del archivo subido no se usa jamás para construir la ruta: se
  genera uno nuevo. Así `../../etc/passwd` no es un nombre, es solo texto que se tira.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

MAXIMO_BYTES = 5 * 1024 * 1024
TROZO = 64 * 1024

# Firma binaria -> extensión. WebP necesita además "WEBP" en el byte 8.
FIRMAS = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
}

FORMATOS_ACEPTADOS = "JPG, PNG, GIF o WebP"


def _extension_real(cabecera: bytes) -> str | None:
    for firma, extension in FIRMAS.items():
        if cabecera.startswith(firma):
            return extension
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return ".webp"
    return None


def _carpeta_de_posts() -> Path:
    carpeta = Path(get_settings().media_root) / "posts"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


async def guardar_imagen_de_post(archivo: UploadFile) -> str:
    """Guarda la imagen y devuelve la URL con la que el frontend la pide.

    Lanza 400 si no es una imagen de un formato aceptado o si pasa del tamaño máximo.
    """
    cabecera = await archivo.read(32)
    extension = _extension_real(cabecera)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo no es una imagen reconocible. Formatos aceptados: {FORMATOS_ACEPTADOS}.",
        )

    destino = _carpeta_de_posts() / f"{uuid.uuid4().hex}{extension}"
    escritos = 0
    try:
        with destino.open("wb") as salida:
            salida.write(cabecera)
            escritos += len(cabecera)
            while trozo := await archivo.read(TROZO):
                escritos += len(trozo)
                if escritos > MAXIMO_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"La imagen pasa de {MAXIMO_BYTES // (1024 * 1024)} MB.",
                    )
                salida.write(trozo)
    except Exception:
        # Un archivo a medias es peor que ninguno: ocuparía disco y se serviría roto.
        destino.unlink(missing_ok=True)
        raise

    settings = get_settings()
    return f"{settings.media_url_base}/posts/{destino.name}"


def ruta_de_media(relativa: str) -> Path:
    """Resuelve una ruta pedida por el navegador dentro de la carpeta de medios.

    `relativa` viene de la URL, así que es entrada no confiable: se resuelve y se
    comprueba que el resultado siga estando dentro de la carpeta. Sin esto,
    `../../app/core/config.py` serviría el código fuente.
    """
    raiz = Path(get_settings().media_root).resolve()
    destino = (raiz / relativa).resolve()
    if raiz not in destino.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    if not destino.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return destino
