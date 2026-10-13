from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.utils import slugify
from app.models.cargo import Cargo
from app.models.tipo_contrato import TipoContrato
from app.models.usuario import Usuario
from app.models.vacante import TokenLinkedIn, Vacante
from app.schemas.vacante import (
    CambioDeEstado,
    CambioDeEstadoDelPost,
    EnvioInternoOut,
    ImagenSubidaOut,
    ResultadoDePublicacion,
    VacanteCreate,
    VacanteOut,
    VistaPreviaDelPost,
    WhatsAppShareOut,
)
from app.services import almacenamiento_service, configuracion_service, correo_service, linkedin_service
from app.services import whatsapp_service

router = APIRouter()


def _origen_del_frontend(request: Request) -> str:
    return request.headers.get("origin") or get_settings().frontend_origin


def _url_publica(request: Request, vacante: Vacante) -> str:
    return f"{_origen_del_frontend(request)}/postular/{vacante.slug}"


def _a_salida(vacante: Vacante, request: Request | None = None) -> VacanteOut:
    salida = VacanteOut.model_validate(vacante)
    salida.tipo_contrato_nombre = vacante.tipo_contrato.nombre if vacante.tipo_contrato else None
    if request is not None:
        salida.url_publica = _url_publica(request, vacante)
    return salida


def _con_relaciones(query):
    return query.options(selectinload(Vacante.tipo_contrato), selectinload(Vacante.cargo))


def _vacante_o_404(db: Session, vacante_id: UUID) -> Vacante:
    vacante = db.scalar(_con_relaciones(select(Vacante)).where(Vacante.id == vacante_id))
    if vacante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")
    return vacante


def _validar_referencias(db: Session, payload: VacanteCreate) -> Cargo:
    cargo = db.get(Cargo, payload.cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cargo seleccionado no existe")
    if not cargo.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El cargo '{cargo.nombre}' está desactivado: actívalo antes de abrir una vacante",
        )
    if payload.tipo_contrato_id is not None and db.get(TipoContrato, payload.tipo_contrato_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El tipo de contrato seleccionado no existe"
        )
    return cargo


def _aplicar(vacante: Vacante, payload: VacanteCreate) -> None:
    datos = payload.model_dump()
    datos["campos_personalizados"] = [c.model_dump() for c in payload.campos_personalizados]
    datos["destinatarios_internos"] = [str(c) for c in payload.destinatarios_internos]
    for campo, valor in datos.items():
        setattr(vacante, campo, valor)


@router.get("", response_model=list[VacanteOut])
def listar_vacantes(
    request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> list[VacanteOut]:
    vacantes = db.scalars(_con_relaciones(select(Vacante)).order_by(Vacante.creado_en.desc())).all()
    return [_a_salida(v, request) for v in vacantes]


@router.post("", response_model=VacanteOut, status_code=status.HTTP_201_CREATED)
def crear_vacante(
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    cargo = _validar_referencias(db, payload)

    vacante = Vacante(
        # El título se copia del cargo: de él sale el slug, que es la URL pública.
        titulo=cargo.nombre,
        slug=slugify(cargo.nombre),
        empleador_id=current_user.id,
    )
    _aplicar(vacante, payload)
    db.add(vacante)
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante.id), request)


@router.put("/{vacante_id}", response_model=VacanteOut)
def actualizar_vacante(
    vacante_id: UUID,
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Actualiza el contenido. El slug **no** se recalcula: ya está repartido."""
    vacante = _vacante_o_404(db, vacante_id)
    _validar_referencias(db, payload)
    _aplicar(vacante, payload)
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.patch("/{vacante_id}/estado", response_model=VacanteOut)
def cambiar_estado(
    vacante_id: UUID,
    payload: CambioDeEstado,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    vacante = _vacante_o_404(db, vacante_id)
    vacante.estado = payload.estado
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.patch("/{vacante_id}/post-estado", response_model=VacanteOut)
def cambiar_estado_del_post(
    vacante_id: UUID,
    payload: CambioDeEstadoDelPost,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Mover el post entre borrador y programado a mano.

    No sirve para marcarlo 'publicado': eso solo lo pone el publicador, porque si no
    la pantalla diría que salió algo que nunca salió.
    """
    vacante = _vacante_o_404(db, vacante_id)
    if payload.post_estado == "publicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'publicado' no se pone a mano: resulta de publicar de verdad",
        )
    if payload.post_estado == "programado" and vacante.post_programado_para is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para programar el post hace falta una fecha y hora de publicación",
        )
    vacante.post_estado = payload.post_estado
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.post("/imagen", response_model=ImagenSubidaOut)
async def subir_imagen_de_post(
    archivo: UploadFile = File(...),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ImagenSubidaOut:
    """Sube la imagen y devuelve su URL, que luego se guarda en la vacante."""
    return ImagenSubidaOut(url=await almacenamiento_service.guardar_imagen_de_post(archivo))


def _texto_del_post(vacante: Vacante, enlace: str) -> str:
    partes = [vacante.asunto or vacante.titulo, "", vacante.post_cuerpo or vacante.descripcion]
    if vacante.remuneracion is not None:
        partes.append(f"Remuneración: ${vacante.remuneracion:,.2f}")
    if vacante.hora_entrada and vacante.hora_salida:
        partes.append(f"Horario: {vacante.hora_entrada:%H:%M} a {vacante.hora_salida:%H:%M}")
    if vacante.tipo_contrato:
        partes.append(f"Tipo de contrato: {vacante.tipo_contrato.nombre}")
    for campo in vacante.campos_personalizados or []:
        if campo.get("valor"):
            partes.append(f"{campo['etiqueta']}: {campo['valor']}")
    partes += ["", f"Postula aquí: {enlace}"]
    return "\n".join(partes)


@router.get("/{vacante_id}/vista-previa", response_model=VistaPreviaDelPost)
def vista_previa_del_post(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> VistaPreviaDelPost:
    """Cómo se verá el post. Es el mismo texto que se publica, no una aproximación."""
    vacante = _vacante_o_404(db, vacante_id)
    enlace = _url_publica(request, vacante)
    texto = _texto_del_post(vacante, enlace)
    return VistaPreviaDelPost(
        asunto=vacante.asunto or vacante.titulo,
        cuerpo=texto,
        imagen_url=vacante.post_imagen_url,
        enlace_para_postular=enlace,
        visibilidad=vacante.visibilidad,
        destinatarios_internos=vacante.destinatarios_internos or [],
        programado_para=vacante.post_programado_para,
        caracteres=len(texto),
    )


@router.post("/{vacante_id}/publicar-linkedin", response_model=ResultadoDePublicacion)
def publicar_en_linkedin(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    vacante = _vacante_o_404(db, vacante_id)
    if vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una vacante interna no se publica en LinkedIn. Cámbiala a pública o mixta.",
        )

    enlace = _url_publica(request, vacante)
    texto = _texto_del_post(vacante, enlace)

    # Sin credenciales, modo simulado: recorre el flujo entero y lo deja marcado como
    # tal, para no hacer creer que algo salió a internet cuando no salió.
    if not linkedin_service.esta_configurado(db):
        vacante.linkedin_post_id = linkedin_service._publicar_simulado(vacante.id, vacante.titulo)
        vacante.post_estado = "publicado"
        vacante.post_publicado_en = datetime.now(timezone.utc)
        vacante.post_error = None
        db.commit()
        return ResultadoDePublicacion(
            post_estado="publicado",
            linkedin_post_id=vacante.linkedin_post_id,
            simulado=True,
            mensaje="LinkedIn no está configurado: se simuló la publicación. No salió nada a internet.",
        )

    token = db.get(TokenLinkedIn, current_user.id)
    if token is None or token.revocado or token.expira_en <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conecta tu cuenta de LinkedIn en Configuración (o vuelve a conectarla: el acceso caducó)",
        )

    from app.services.configuracion_service import _cifrador

    try:
        access_token = _cifrador().decrypt(token.access_token_cifrado.encode()).decode()
        post_id = linkedin_service.publicar_en_el_muro(
            access_token=access_token,
            persona_urn=token.persona_urn,
            texto=texto,
            enlace=enlace,
        )
    except httpx.HTTPError as error:
        vacante.post_estado = "error"
        vacante.post_error = str(error)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó la publicación: {error}")

    vacante.linkedin_post_id = post_id
    vacante.post_estado = "publicado"
    vacante.post_publicado_en = datetime.now(timezone.utc)
    vacante.post_error = None
    db.commit()
    return ResultadoDePublicacion(
        post_estado="publicado",
        linkedin_post_id=post_id,
        simulado=False,
        mensaje="Publicado en LinkedIn.",
    )


@router.post("/{vacante_id}/enviar-interno", response_model=EnvioInternoOut)
def enviar_internamente(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> EnvioInternoOut:
    vacante = _vacante_o_404(db, vacante_id)
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

    enlace = _url_publica(request, vacante)
    texto = _texto_del_post(vacante, enlace)
    html = "<p>" + texto.replace("\n", "<br>") + "</p>"
    try:
        enviados = correo_service.enviar(
            db,
            destinatarios=destinatarios,
            asunto=vacante.asunto or vacante.titulo,
            cuerpo_html=html,
            cuerpo_texto=texto,
        )
    except OSError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"No se pudo enviar: {error}")

    vacante.enviado_internamente_en = datetime.now(timezone.utc)
    db.commit()
    return EnvioInternoOut(enviados=enviados, mensaje=f"Enviado a {enviados} destinatario(s).")


@router.get("/{vacante_id}/share-whatsapp", response_model=WhatsAppShareOut)
def compartir_whatsapp(
    vacante_id: UUID, request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> WhatsAppShareOut:
    vacante = _vacante_o_404(db, vacante_id)
    return WhatsAppShareOut(
        whatsapp_url=whatsapp_service.build_share_link(vacante.titulo, _url_publica(request, vacante))
    )
