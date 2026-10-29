"""Sirve los archivos de un candidato: su foto y su CV.

Separado de `/media` a propósito. Aquella ruta va sin autenticación porque la imagen
de un post tiene que poder verla LinkedIn, que no trae el token de nadie. La foto y el
CV de una persona no son eso: son datos personales, y un nombre de archivo difícil de
adivinar no es un control de acceso.

Quien pide aquí tiene que haber iniciado sesión. El candidato no necesita esta ruta:
ve su propia foto desde el archivo que acaba de elegir, sin pedirla de vuelta.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services import almacenamiento_service

router = APIRouter()


@router.get("/postulantes/{nombre}")
def servir_archivo_de_candidato(nombre: str, _: Usuario = Depends(get_current_user)) -> FileResponse:
    destino = almacenamiento_service.ruta_de_candidato(nombre)
    return FileResponse(destino)
