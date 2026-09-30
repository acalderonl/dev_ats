from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.postulacion import PipelineStatusUpdate, PostulacionOut
from app.services.pipeline_service import validate_transition

router = APIRouter()


@router.get("", response_model=list[PostulacionOut])
def listar_postulaciones(
    vacante_id: UUID | None = None,
    estado_pipeline: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[PostulacionOut]:
    query = select(Postulacion).options(selectinload(Postulacion.postulante), selectinload(Postulacion.vacante))
    if vacante_id is not None:
        query = query.where(Postulacion.vacante_id == vacante_id)
    if estado_pipeline is not None:
        query = query.where(Postulacion.estado_pipeline == estado_pipeline)
    postulaciones = db.scalars(query.order_by(Postulacion.creado_en.desc())).all()
    return [PostulacionOut.from_orm_enriquecido(p) for p in postulaciones]


def _get_postulacion_or_404(db: Session, postulacion_id: UUID) -> Postulacion:
    postulacion = db.scalar(
        select(Postulacion)
        .options(selectinload(Postulacion.postulante), selectinload(Postulacion.vacante))
        .where(Postulacion.id == postulacion_id)
    )
    if postulacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")
    return postulacion


@router.post("/{postulacion_id}/autorizar", response_model=PostulacionOut)
def autorizar_postulacion(
    postulacion_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> PostulacionOut:
    postulacion = _get_postulacion_or_404(db, postulacion_id)
    if postulacion.estado_pipeline != "pendiente_autorizacion":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La postulación ya fue autorizada")

    postulacion.autorizado_por = current_user.id
    postulacion.fecha_autorizacion = datetime.now(timezone.utc)
    postulacion.estado_pipeline = "postulacion_revisada"
    db.commit()
    db.refresh(postulacion)
    return PostulacionOut.from_orm_enriquecido(postulacion)


@router.patch("/{postulacion_id}/pipeline-status", response_model=PostulacionOut)
def actualizar_estado_pipeline(
    postulacion_id: UUID,
    payload: PipelineStatusUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> PostulacionOut:
    postulacion = _get_postulacion_or_404(db, postulacion_id)
    validate_transition(postulacion.estado_pipeline, payload.estado_pipeline)
    postulacion.estado_pipeline = payload.estado_pipeline
    db.commit()
    db.refresh(postulacion)
    return PostulacionOut.from_orm_enriquecido(postulacion)
