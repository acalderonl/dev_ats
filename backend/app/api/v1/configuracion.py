"""Pantalla de Configuración: credenciales, jornadas y la conexión con LinkedIn.

Todo lo de aquí es de `super_admin`. Un reclutador publica vacantes; cambiar con qué
cuenta de LinkedIn o desde qué correo sale la empresa es otra cosa.

Ningún endpoint devuelve un secreto. Se devuelve si está configurado y una pista de
cuatro caracteres, que es lo justo para reconocerlo.
"""

import smtplib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.jornada import Jornada
from app.models.usuario import Usuario
from app.models.vacante import TokenLinkedIn
from app.schemas.configuracion import (
    ConfiguracionOut,
    ConfiguracionUpdate,
    EstadoLinkedIn,
    JornadaCreate,
    JornadaOut,
    JornadaUpdate,
    PruebaDeCorreo,
    UrlDeConexion,
)
from app.services import configuracion_service, correo_service, linkedin_service

router = APIRouter()


@router.get("", response_model=ConfiguracionOut)
def leer_configuracion(
    db: Session = Depends(get_db), _: Usuario = Depends(require_roles("super_admin"))
) -> ConfiguracionOut:
    return ConfiguracionOut(**configuracion_service.estado_de_configuracion(db))


@router.put("", response_model=ConfiguracionOut)
def guardar_configuracion(
    payload: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> ConfiguracionOut:
    """Guarda solo lo que viene.

    Un campo ausente **no se toca**: así la pantalla puede mandar el formulario entero
    sin borrar un secreto que no se reescribió (los secretos nunca se devuelven, así
    que el formulario los manda vacíos).
    """
    for clave, valor in payload.model_dump(exclude_unset=True).items():
        configuracion_service.escribir(db, clave, valor)
    db.commit()
    return ConfiguracionOut(**configuracion_service.estado_de_configuracion(db))


# -------------------------------------------------------------------------- Correo


@router.post("/correo/probar", response_model=PruebaDeCorreo)
def probar_correo(db: Session = Depends(get_db), _: Usuario = Depends(require_roles("super_admin"))) -> PruebaDeCorreo:
    """Se conecta y autentica sin enviar nada.

    Devuelve 200 con `ok: false` cuando la conexión falla, en vez de un error: que el
    servidor rechace la contraseña es una respuesta legítima de esta prueba, no un
    fallo de la aplicación. La pantalla muestra el motivo.
    """
    try:
        return PruebaDeCorreo(ok=True, mensaje=correo_service.probar(db))
    except correo_service.CorreoNoConfigurado as error:
        return PruebaDeCorreo(ok=False, mensaje=str(error))
    except smtplib.SMTPAuthenticationError:
        return PruebaDeCorreo(
            ok=False,
            mensaje="El servidor rechazó el usuario o la contraseña. "
            "En Gmail recuerda que debe ser una contraseña de aplicación, no la de la cuenta.",
        )
    except (OSError, smtplib.SMTPException) as error:
        return PruebaDeCorreo(ok=False, mensaje=f"No se pudo conectar: {error}")


# ------------------------------------------------------------------------ LinkedIn


@router.get("/linkedin/estado", response_model=EstadoLinkedIn)
def estado_de_linkedin(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)) -> EstadoLinkedIn:
    """Si la aplicación tiene credenciales y si **este** usuario conectó su cuenta."""
    token = db.get(TokenLinkedIn, usuario.id)
    vigente = bool(token and not token.revocado and token.expira_en > datetime.now(timezone.utc))
    return EstadoLinkedIn(
        credenciales_configuradas=linkedin_service.esta_configurado(db),
        cuenta_conectada=vigente,
        nombre_en_linkedin=token.nombre_en_linkedin if token else None,
        expira_en=token.expira_en if token else None,
        correo_configurado=correo_service.esta_configurado(db),
    )


@router.post("/linkedin/conectar", response_model=UrlDeConexion)
def iniciar_conexion(
    db: Session = Depends(get_db), _: Usuario = Depends(require_roles("super_admin", "reclutador"))
) -> UrlDeConexion:
    try:
        url, state = linkedin_service.url_de_autorizacion(db)
    except linkedin_service.LinkedInNoConfigurado as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    return UrlDeConexion(url=url, state=state)


@router.delete("/linkedin/desconectar", status_code=status.HTTP_204_NO_CONTENT)
def desconectar(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)) -> None:
    token = db.get(TokenLinkedIn, usuario.id)
    if token is not None:
        db.delete(token)
        db.commit()


# ------------------------------------------------------------------------ Jornadas


@router.get("/jornadas", response_model=list[JornadaOut])
def listar_jornadas(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)) -> list[JornadaOut]:
    """La lee cualquiera: el formulario de vacante la necesita para el selector."""
    return db.scalars(select(Jornada).order_by(Jornada.horas.desc())).all()


@router.post("/jornadas", response_model=JornadaOut, status_code=status.HTTP_201_CREATED)
def crear_jornada(
    payload: JornadaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> JornadaOut:
    if db.scalar(select(Jornada).where(Jornada.nombre == payload.nombre)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe una jornada '{payload.nombre}'")
    jornada = Jornada(**payload.model_dump())
    db.add(jornada)
    db.commit()
    db.refresh(jornada)
    return jornada


@router.put("/jornadas/{jornada_id}", response_model=JornadaOut)
def actualizar_jornada(
    jornada_id: int,
    payload: JornadaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> JornadaOut:
    jornada = db.get(Jornada, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(jornada, campo, valor)
    db.commit()
    db.refresh(jornada)
    return jornada


@router.delete("/jornadas/{jornada_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_jornada(
    jornada_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin")),
) -> None:
    """Se puede borrar sin romper nada: la vacante copia las horas, no la referencia."""
    jornada = db.get(Jornada, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    db.delete(jornada)
    db.commit()
