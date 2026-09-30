from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.evaluacion import Evaluacion
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.evaluacion import EvaluacionCreate, EvaluacionOut

router = APIRouter()


@router.get("/{postulacion_id}/evaluaciones", response_model=list[EvaluacionOut])
def listar_evaluaciones(
    postulacion_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador", "entrevistador")),
) -> list[EvaluacionOut]:
    return db.scalars(select(Evaluacion).where(Evaluacion.postulacion_id == postulacion_id)).all()


@router.post("/{postulacion_id}/evaluaciones", response_model=EvaluacionOut, status_code=status.HTTP_201_CREATED)
def crear_evaluacion(
    postulacion_id: UUID,
    payload: EvaluacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador", "entrevistador")),
) -> EvaluacionOut:
    postulacion = db.get(Postulacion, postulacion_id)
    if postulacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada")

    evaluacion = Evaluacion(
        postulacion_id=postulacion_id,
        evaluador_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(evaluacion)
    db.commit()
    db.refresh(evaluacion)
    return evaluacion
