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


def _dentro_de(raiz: Path, carpeta: str, relativa: str) -> Path:
    """Resuelve `relativa` y exige que caiga dentro de `raiz/carpeta`.

    `relativa` viene de la URL, así que es entrada no confiable: se resuelve y se
    comprueba el resultado. Sin esto, `../../app/core/config.py` serviría el código
    fuente, y `../postulantes/x.pdf` sacaría por la puerta pública el CV de alguien.
    """
    permitida = (raiz / carpeta).resolve()
    destino = (raiz / relativa).resolve()
    if permitida != destino and permitida not in destino.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    if not destino.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return destino


def ruta_de_media(relativa: str) -> Path:
    """La ruta de un archivo **público**: solo la carpeta de los posts.

    La lista blanca es lo que impide que la ruta sin autenticar sirva la foto o el CV
    de un candidato: aunque se adivinara el nombre, no está en la carpeta permitida.
    """
    return _dentro_de(Path(get_settings().media_root).resolve(), CARPETA_PUBLICA, relativa)


def ruta_de_candidato(nombre: str) -> Path:
    """La ruta de un archivo de un candidato. Quien llame aquí ya pidió sesión.

    Recibe el nombre suelto, no la carpeta: la ruta que lo sirve ya la fija. Si el
    nombre trae `..` para salirse, la comprobación de `_dentro_de` lo corta igual.
    """
    raiz = Path(get_settings().media_root).resolve()
    return _dentro_de(raiz, CARPETA_DE_CANDIDATOS, f"{CARPETA_DE_CANDIDATOS}/{nombre}")


# --------------------------------------------- Archivos de un candidato (privados)

# La foto y el CV de una persona no son la imagen de un post: no pueden colgar de una
# URL que cualquiera abra. Van a su propia carpeta, `ruta_de_media` se niega a
# servirlas, y salen por `/api/v1/archivos`, que sí pide sesión.
CARPETA_PUBLICA = "posts"
CARPETA_DE_CANDIDATOS = "postulantes"

MAXIMO_BYTES_DE_CV = 15 * 1024 * 1024

# Firma binaria -> extensión, para los adjuntos. El `.doc` binario antiguo no entra:
# el lector de CV tampoco lo soporta, y aceptarlo aquí sería prometer algo a medias.
FIRMAS_DE_DOCUMENTO = {
    b"%PDF-": ".pdf",
    # .docx es un zip; la extensión se queda en .docx porque es lo que se subió.
    b"PK\x03\x04": ".docx",
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
}

FORMATOS_DE_CV = "PDF, DOCX, JPG o PNG"


def _carpeta(nombre: str) -> Path:
    carpeta = Path(get_settings().media_root) / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


async def _guardar(
    archivo: UploadFile,
    *,
    carpeta: str,
    extension: str,
    maximo: int,
) -> Path:
    """Escribe a trozos y borra lo escrito si algo falla.

    Se separa de quien decide la extensión porque esa decisión es distinta para una
    imagen y para un adjunto, pero escribir con cuidado es lo mismo en los dos casos.

    Pasarse de tamaño responde **413**, que es lo que ya devolvía el lector de CV y lo
    que significa de verdad «demasiado grande». La imagen del post sigue con su 400
    porque tiene su propia escritura y hay pantallas contando con ese código.
    """
    destino = _carpeta(carpeta) / f"{uuid.uuid4().hex}{extension}"
    escritos = 0
    try:
        with destino.open("wb") as salida:
            while trozo := await archivo.read(TROZO):
                escritos += len(trozo)
                if escritos > maximo:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"El archivo pasa de {maximo // (1024 * 1024)} MB.",
                    )
                salida.write(trozo)
    except Exception:
        destino.unlink(missing_ok=True)
        raise
    return destino


def _url_privada(destino: Path) -> str:
    return f"/api/v1/archivos/{CARPETA_DE_CANDIDATOS}/{destino.name}"


async def guardar_foto_de_candidato(archivo: UploadFile) -> str:
    """Guarda la foto del candidato y devuelve la URL con la que se pide."""
    cabecera = await archivo.read(32)
    extension = _extension_real(cabecera)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo no es una imagen reconocible. Formatos aceptados: {FORMATOS_ACEPTADOS}.",
        )
    await archivo.seek(0)
    destino = await _guardar(archivo, carpeta=CARPETA_DE_CANDIDATOS, extension=extension, maximo=MAXIMO_BYTES)
    return _url_privada(destino)


async def guardar_cv(archivo: UploadFile) -> str:
    """Guarda el CV tal cual se subió y devuelve su URL.

    Hasta ahora el CV se leía en memoria y se tiraba: quedaba lo que la extracción
    hubiera entendido y nada con qué contrastarlo.
    """
    cabecera = await archivo.read(8)
    extension = next((e for f, e in FIRMAS_DE_DOCUMENTO.items() if cabecera.startswith(f)), None)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se reconoce el archivo. Formatos aceptados: {FORMATOS_DE_CV}.",
        )
    await archivo.seek(0)
    destino = await _guardar(archivo, carpeta=CARPETA_DE_CANDIDATOS, extension=extension, maximo=MAXIMO_BYTES_DE_CV)
    return _url_privada(destino)
