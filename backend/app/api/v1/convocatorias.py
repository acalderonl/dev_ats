"""Convocatorias: el ciclo de una vacante, y todo lo que se hace con su post.

Aquí vive lo que antes colgaba de `/vacantes/{id}/...`: cambiar el estado, el post,
la vista previa, compartir y publicar en LinkedIn, el envío interno y WhatsApp. Se
movió porque todo eso es **de una ronda**, no del puesto: una vacante convocada tres
veces tiene tres posts, tres enlaces y tres listas de postulantes.

Las condiciones del puesto se leen de `convocatoria.vacante`.
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.convocatoria import Convocatoria
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.models.vacante import TokenLinkedIn, Vacante
from app.schemas.convocatoria import (
    CambioDeEstado,
    CambioDeEstadoDelPost,
    ConvocatoriaCreate,
    ConvocatoriaOut,
    EnvioInternoOut,
    ParaCompartirEnLinkedIn,
    ResultadoDePublicacion,
    VistaPreviaDelPost,
    WhatsAppShareOut,
)
from app.services import almacenamiento_service, configuracion_service, correo_service, linkedin_service
from app.services import post_service, whatsapp_service

router = APIRouter()


# ------------------------------------------------------------------ Helpers


def con_relaciones(query):
    """Todo lo que hace falta para armar el post sin consultas sueltas."""
    return query.options(
        selectinload(Convocatoria.vacante).selectinload(Vacante.tipo_contrato),
        selectinload(Convocatoria.vacante).selectinload(Vacante.cargo),
    )


def convocatoria_o_404(db: Session, convocatoria_id: UUID) -> Convocatoria:
    convocatoria = db.scalar(con_relaciones(select(Convocatoria)).where(Convocatoria.id == convocatoria_id))
    if convocatoria is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convocatoria no encontrada")
    return convocatoria


def a_salida(db: Session, convocatoria: Convocatoria, request: Request | None = None) -> ConvocatoriaOut:
    salida = ConvocatoriaOut.model_validate(convocatoria)
    salida.postulantes = (
        db.scalar(select(func.count()).select_from(Postulacion).where(Postulacion.convocatoria_id == convocatoria.id))
        or 0
    )
    if request is not None:
        salida.url_publica = post_service.url_publica(request, convocatoria)
    return salida


def aplicar(convocatoria: Convocatoria, payload: ConvocatoriaCreate) -> None:
    for campo, valor in payload.model_dump().items():
        setattr(convocatoria, campo, valor)


# ------------------------------------------------------------- Editar el ciclo


@router.put("/{convocatoria_id}", response_model=ConvocatoriaOut)
def actualizar_convocatoria(
    convocatoria_id: UUID,
    payload: ConvocatoriaCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ConvocatoriaOut:
    """Cambia fecha, estado y post. El slug **no** se recalcula: ya está repartido."""
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    aplicar(convocatoria, payload)
    db.commit()
    return a_salida(db, convocatoria_o_404(db, convocatoria_id), request)


@router.patch("/{convocatoria_id}/estado", response_model=ConvocatoriaOut)
def cambiar_estado(
    convocatoria_id: UUID,
    payload: CambioDeEstado,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ConvocatoriaOut:
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    convocatoria.estado = payload.estado
    db.commit()
    return a_salida(db, convocatoria_o_404(db, convocatoria_id), request)


@router.patch("/{convocatoria_id}/post-estado", response_model=ConvocatoriaOut)
def cambiar_estado_del_post(
    convocatoria_id: UUID,
    payload: CambioDeEstadoDelPost,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ConvocatoriaOut:
    """Mover el post entre borrador y programado a mano.

    No sirve para marcarlo 'publicado': eso solo lo pone el publicador, porque si no
    la pantalla diría que salió algo que nunca salió.
    """
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    if payload.post_estado == "publicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'publicado' no se pone a mano: resulta de publicar de verdad",
        )
    if payload.post_estado == "programado" and convocatoria.post_programado_para is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para programar el post hace falta una fecha y hora de publicación",
        )
    convocatoria.post_estado = payload.post_estado
    db.commit()
    return a_salida(db, convocatoria_o_404(db, convocatoria_id), request)


# ------------------------------------------------------------------ El post


@router.get("/{convocatoria_id}/vista-previa", response_model=VistaPreviaDelPost)
def vista_previa_del_post(
    convocatoria_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VistaPreviaDelPost:
    """Cómo se verá el post. Es el mismo texto que se publica, no una aproximación."""
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    return post_service.armar_vista_previa(
        convocatoria, post_service.url_publica(request, convocatoria), post_service.nombre_de_quien_publica(db, usuario)
    )


def _compartible_o_400(convocatoria: Convocatoria) -> None:
    """Lo que no debe salir, no sale: ni una interna ni una que no esté abierta."""
    if convocatoria.vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una vacante interna no se publica en LinkedIn. Cámbiala a pública o mixta.",
        )
    if convocatoria.estado != "abierta":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se comparte una convocatoria abierta: LinkedIn mostraría una tarjeta que lleva a un 404.",
        )


@router.post("/{convocatoria_id}/compartir-linkedin", response_model=ParaCompartirEnLinkedIn)
def preparar_para_compartir(
    convocatoria_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ParaCompartirEnLinkedIn:
    """Prepara el contenido y el enlace para publicar a mano en LinkedIn.

    Es la vía sin OAuth: el sistema arma el texto y abre el compositor de LinkedIn con
    la tarjeta de la vacante; quien publica es la persona, desde su propia cuenta.

    El enlace que se le da a LinkedIn es el de `/compartir/{slug}`, la página con las
    etiquetas Open Graph, no el del formulario: la aplicación es una SPA y al rastreador
    le llegaría un `<div id="root">` vacío.
    """
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    _compartible_o_400(convocatoria)

    origen = post_service.origen_del_frontend(request).rstrip("/")
    enlace_para_linkedin = f"{origen}/compartir/{convocatoria.slug}"
    texto = post_service.texto_del_post(convocatoria, post_service.url_publica(request, convocatoria))

    # "compartido", no "publicado": quien pulsa Publicar es la persona.
    convocatoria.post_estado = "compartido"
    db.commit()

    compositor = "https://www.linkedin.com/sharing/share-offsite/?url=" + quote(enlace_para_linkedin, safe="")
    return ParaCompartirEnLinkedIn(
        texto=texto,
        enlace_de_la_vacante=enlace_para_linkedin,
        url_del_compositor=compositor,
        aviso=(
            "LinkedIn arma la tarjeta a partir del enlace y no admite texto preparado, así que el "
            "texto se copió al portapapeles: pégalo en el compositor y pulsa Publicar."
        ),
    )


def _miniatura_para_linkedin(
    convocatoria: Convocatoria, access_token: str, persona_urn: str
) -> tuple[str | None, str | None]:
    """Sube la imagen del post a LinkedIn y devuelve (urn, aviso).

    Ninguno de los problemas posibles aquí tumba la publicación: una vacante sin
    tarjeta se ve peor, pero no publicarla por la foto sería peor todavía. Lo que no
    se hace, se dice en el aviso que vuelve a la pantalla.
    """
    if not convocatoria.post_imagen_url:
        return None, None

    extension = Path(convocatoria.post_imagen_url).suffix.lower()
    if extension not in linkedin_service.FORMATOS_DE_IMAGEN_EN_LINKEDIN:
        return None, f"La imagen no se envió: LinkedIn no acepta {extension or 'ese formato'}, solo JPG, PNG o GIF."

    # La imagen vive en nuestro volumen; LinkedIn necesita los bytes, no la URL.
    relativa = convocatoria.post_imagen_url.split("/media/", 1)[-1]
    try:
        ruta = almacenamiento_service.ruta_de_media(relativa)
        contenido = ruta.read_bytes()
    except (HTTPException, OSError):
        return None, "La imagen no se envió: no se encontró el archivo en el servidor."

    try:
        urn = linkedin_service.subir_imagen(
            access_token=access_token, persona_urn=persona_urn, contenido=contenido, nombre=ruta.name
        )
    except httpx.HTTPError as error:
        return None, f"La imagen no se envió: LinkedIn la rechazó ({error})."

    return urn, None


@router.post("/{convocatoria_id}/publicar-linkedin", response_model=ResultadoDePublicacion)
def publicar_en_linkedin(
    convocatoria_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    vacante = convocatoria.vacante
    if vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una vacante interna no se publica en LinkedIn. Cámbiala a pública o mixta.",
        )

    enlace = post_service.url_publica(request, convocatoria)
    texto = post_service.texto_del_post(convocatoria, enlace)

    # Quien manda es el token, no las credenciales de la aplicación: uno pegado a mano
    # desde el portal de LinkedIn publica de verdad aunque no haya Client Secret ni
    # Redirect URI guardados.
    token = db.get(TokenLinkedIn, current_user.id)
    token_usable = token is not None and not token.revocado and token.expira_en > datetime.now(timezone.utc)

    if not token_usable:
        if token is not None or linkedin_service.esta_configurado(db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conecta tu cuenta de LinkedIn en Configuración (o vuelve a conectarla: el acceso caducó)",
            )
        # Sin token y sin credenciales, modo simulado: recorre el flujo entero y lo
        # deja marcado como tal, para no hacer creer que algo salió a internet.
        convocatoria.linkedin_post_id = linkedin_service._publicar_simulado(convocatoria.id, vacante.titulo)
        convocatoria.post_estado = "publicado"
        convocatoria.post_publicado_en = datetime.now(timezone.utc)
        convocatoria.post_error = None
        db.commit()
        return ResultadoDePublicacion(
            post_estado="publicado",
            linkedin_post_id=convocatoria.linkedin_post_id,
            simulado=True,
            mensaje="LinkedIn no está configurado: se simuló la publicación. No salió nada a internet.",
        )

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    imagen_urn, aviso_de_imagen = _miniatura_para_linkedin(convocatoria, access_token, token.persona_urn)

    try:
        post_id = linkedin_service.publicar_en_el_muro(
            access_token=access_token,
            persona_urn=token.persona_urn,
            texto=texto,
            enlace=enlace,
            titulo=convocatoria.asunto or vacante.titulo,
            descripcion=convocatoria.post_cuerpo or vacante.descripcion,
            imagen_urn=imagen_urn,
        )
    except httpx.HTTPError as error:
        convocatoria.post_estado = "error"
        convocatoria.post_error = str(error)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó la publicación: {error}")

    convocatoria.linkedin_post_id = post_id
    convocatoria.post_estado = "publicado"
    convocatoria.post_publicado_en = datetime.now(timezone.utc)
    convocatoria.post_error = None
    db.commit()
    return ResultadoDePublicacion(
        post_estado="publicado",
        linkedin_post_id=post_id,
        simulado=False,
        mensaje="Publicado en LinkedIn." + (f" {aviso_de_imagen}" if aviso_de_imagen else ""),
    )


def _token_usable_o_400(db: Session, usuario: Usuario) -> TokenLinkedIn:
    """El token de quien pide, o un 400 que dice qué hacer."""
    token = db.get(TokenLinkedIn, usuario.id)
    if token is None or token.revocado or token.expira_en <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conecta tu cuenta de LinkedIn en Configuración (o vuelve a conectarla: el acceso caducó)",
        )
    return token


def _post_en_linkedin_o_400(convocatoria: Convocatoria) -> str:
    """El URN del post, descartando el de las publicaciones simuladas."""
    if not convocatoria.linkedin_post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Esta convocatoria no está publicada en LinkedIn."
        )
    if "simulado" in convocatoria.linkedin_post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esa publicación fue simulada: no existe en LinkedIn, así que no hay nada que cambiar allí.",
        )
    return convocatoria.linkedin_post_id


@router.patch("/{convocatoria_id}/linkedin-post", response_model=ResultadoDePublicacion)
def actualizar_post_en_linkedin(
    convocatoria_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    """Reescribe el texto del post con los datos de hoy. Es lo único que LinkedIn deja cambiar."""
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    post_urn = _post_en_linkedin_o_400(convocatoria)
    token = _token_usable_o_400(db, current_user)

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    texto = post_service.texto_del_post(convocatoria, post_service.url_publica(request, convocatoria))
    try:
        linkedin_service.actualizar_texto(access_token=access_token, post_urn=post_urn, texto=texto)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó el cambio: {error}")

    return ResultadoDePublicacion(
        post_estado=convocatoria.post_estado,
        linkedin_post_id=post_urn,
        simulado=False,
        mensaje="El texto del post se actualizó en LinkedIn. El enlace y la imagen no se pueden cambiar.",
    )


@router.delete("/{convocatoria_id}/linkedin-post", response_model=ResultadoDePublicacion)
def borrar_post_en_linkedin(
    convocatoria_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    """Borra el post de LinkedIn y devuelve el post a borrador."""
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    post_urn = _post_en_linkedin_o_400(convocatoria)
    token = _token_usable_o_400(db, current_user)

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    try:
        linkedin_service.borrar_post(access_token=access_token, post_urn=post_urn)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó el borrado: {error}")

    convocatoria.linkedin_post_id = None
    convocatoria.post_estado = "borrador"
    convocatoria.post_publicado_en = None
    db.commit()
    return ResultadoDePublicacion(
        post_estado="borrador",
        linkedin_post_id=None,
        simulado=False,
        mensaje="El post se borró de LinkedIn y volvió a borrador.",
    )


# ------------------------------------------------------- Otros canales


@router.post("/{convocatoria_id}/enviar-interno", response_model=EnvioInternoOut)
def enviar_internamente(
    convocatoria_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> EnvioInternoOut:
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    vacante = convocatoria.vacante
    if vacante.visibilidad == "publica":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta vacante es pública: no tiene envío interno. Cámbiala a interna o mixta.",
        )
    destinatarios = vacante.destinatarios_internos or []
    if not destinatarios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay destinatarios internos")

    dominios = configuracion_service.dominios_corporativos(db)
    if dominios:
        ajenos = [c for c in destinatarios if c.split("@")[-1].lower() not in dominios]
        if ajenos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estos correos no son de un dominio corporativo ({', '.join(dominios)}): "
                f"{', '.join(ajenos)}",
            )

    if not correo_service.esta_configurado(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta configurar el correo de Gmail en Configuración para poder enviar",
        )

    texto = post_service.texto_del_post(convocatoria, post_service.url_publica(request, convocatoria))
    html = "<p>" + texto.replace("\n", "<br>") + "</p>"
    try:
        enviados = correo_service.enviar(
            db,
            destinatarios=destinatarios,
            asunto=convocatoria.asunto or vacante.titulo,
            cuerpo_html=html,
            cuerpo_texto=texto,
        )
    except OSError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"No se pudo enviar: {error}")

    convocatoria.enviado_internamente_en = datetime.now(timezone.utc)
    db.commit()
    return EnvioInternoOut(enviados=enviados, mensaje=f"Enviado a {enviados} destinatario(s).")


@router.get("/{convocatoria_id}/share-whatsapp", response_model=WhatsAppShareOut)
def compartir_whatsapp(
    convocatoria_id: UUID, request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> WhatsAppShareOut:
    convocatoria = convocatoria_o_404(db, convocatoria_id)
    return WhatsAppShareOut(
        whatsapp_url=whatsapp_service.build_share_link(
            convocatoria.vacante.titulo, post_service.url_publica(request, convocatoria)
        )
    )
