from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.utils import slugify
from app.models.usuario import Usuario
from app.models.vacante import Vacante
from app.schemas.vacante import LinkedInPublishOut, VacanteCreate, VacanteOut, WhatsAppShareOut
from app.services import linkedin_service, whatsapp_service

router = APIRouter()


@router.get("", response_model=list[VacanteOut])
def listar_vacantes(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)) -> list[VacanteOut]:
    return db.scalars(select(Vacante).order_by(Vacante.creado_en.desc())).all()


@router.post("", response_model=VacanteOut, status_code=status.HTTP_201_CREATED)
def crear_vacante(
    payload: VacanteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    vacante = Vacante(
        titulo=payload.titulo,
        cargo_id=payload.cargo_id,
        descripcion=payload.descripcion,
        fecha_limite=payload.fecha_limite,
        slug=slugify(payload.titulo),
        empleador_id=current_user.id,
    )
    db.add(vacante)
    db.commit()
    db.refresh(vacante)
    return vacante


def _get_vacante_or_404(db: Session, vacante_id: UUID) -> Vacante:
    vacante = db.get(Vacante, vacante_id)
    if vacante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")
    return vacante


@router.post("/{vacante_id}/publish-linkedin", response_model=LinkedInPublishOut)
def publicar_linkedin(
    vacante_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> LinkedInPublishOut:
    vacante = _get_vacante_or_404(db, vacante_id)
    post_id = linkedin_service.publish_job_posting(vacante.id, vacante.titulo, vacante.descripcion)
    vacante.linkedin_post_id = post_id
    db.commit()
    return LinkedInPublishOut(linkedin_post_id=post_id)


@router.get("/{vacante_id}/share-whatsapp", response_model=WhatsAppShareOut)
def compartir_whatsapp(
    vacante_id: UUID, request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> WhatsAppShareOut:
    vacante = _get_vacante_or_404(db, vacante_id)
    frontend_origin = request.headers.get("origin") or "http://localhost:3000"
    url_publica = f"{frontend_origin}/postular/{vacante.slug}"
    return WhatsAppShareOut(whatsapp_url=whatsapp_service.build_share_link(vacante.titulo, url_publica))


@router.patch("/{vacante_id}/cerrar", response_model=VacanteOut)
def cerrar_vacante(
    vacante_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    vacante = _get_vacante_or_404(db, vacante_id)
    vacante.estado = "cerrada"
    db.commit()
    db.refresh(vacante)
    return vacante
