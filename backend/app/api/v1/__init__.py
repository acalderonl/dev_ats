from fastapi import APIRouter

from app.api.v1 import (
    auth,
    cargos,
    catalogos,
    competencias,
    configuracion,
    contactos,
    dashboard,
    evaluaciones,
    media,
    postulaciones,
    public,
    usuarios,
    vacantes,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(usuarios.router, prefix="/users", tags=["Usuarios"])
api_router.include_router(cargos.router, prefix="/cargos", tags=["Cargos"])
api_router.include_router(catalogos.router, prefix="/catalogos", tags=["Catálogos"])
api_router.include_router(competencias.router, prefix="/competencias", tags=["Competencias"])
api_router.include_router(vacantes.router, prefix="/vacantes", tags=["Vacantes"])
api_router.include_router(public.router, prefix="/public", tags=["Portal Público"])
api_router.include_router(postulaciones.router, prefix="/postulaciones", tags=["Pipeline"])
api_router.include_router(evaluaciones.router, prefix="/postulaciones", tags=["Evaluaciones"])
api_router.include_router(contactos.router, prefix="/contactos", tags=["Contactos"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(configuracion.router, prefix="/configuracion", tags=["Configuración"])
api_router.include_router(media.router, prefix="/media", tags=["Medios"])
