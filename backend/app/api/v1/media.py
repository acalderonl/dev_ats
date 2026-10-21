"""Sirve las imágenes guardadas en el volumen.

Va sin autenticación a propósito: la imagen del post tiene que poder verse desde el
correo interno y desde LinkedIn, que no traen el token de nadie. El nombre del archivo
es un UUID aleatorio, así que no se puede adivinar; eso es lo que lo protege, no un
candado en la ruta. Nada sensible debe guardarse aquí.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.services import almacenamiento_service

router = APIRouter()


@router.get("/{ruta:path}")
def servir_archivo(ruta: str) -> FileResponse:
    destino = almacenamiento_service.ruta_de_media(ruta)
    return FileResponse(destino)
