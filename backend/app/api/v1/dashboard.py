from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.models.convocatoria import Convocatoria
from app.schemas.dashboard import DashboardMetricsOut, OrigenCount, PipelineEtapaCount

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsOut)
def obtener_metricas(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)) -> DashboardMetricsOut:
    # Se cuentan convocatorias, que es lo que está recibiendo gente. "Activas" son las
    # abiertas y no vencidas; "expiradas", las que siguen marcadas abiertas pero cuya
    # fecha ya pasó —las que alguien debería cerrar o volver a convocar—.
    vacantes_activas = (
        db.scalar(
            select(func.count())
            .select_from(Convocatoria)
            .where(Convocatoria.estado == "abierta", Convocatoria.fecha_limite >= func.now())
        )
        or 0
    )
    vacantes_expiradas = (
        db.scalar(
            select(func.count())
            .select_from(Convocatoria)
            .where(Convocatoria.estado == "abierta", Convocatoria.fecha_limite < func.now())
        )
        or 0
    )
    postulaciones_totales = db.scalar(select(func.count()).select_from(Postulacion)) or 0
    entrevistas_pendientes = (
        db.scalar(select(func.count()).select_from(Postulacion).where(Postulacion.estado_pipeline == "entrevista")) or 0
    )

    por_etapa = db.execute(
        select(Postulacion.estado_pipeline, func.count()).group_by(Postulacion.estado_pipeline)
    ).all()
    por_origen = db.execute(select(Postulacion.origen, func.count()).group_by(Postulacion.origen)).all()

    return DashboardMetricsOut(
        vacantes_activas=vacantes_activas,
        vacantes_expiradas=vacantes_expiradas,
        postulaciones_totales=postulaciones_totales,
        postulaciones_por_etapa=[PipelineEtapaCount(estado=e, total=t) for e, t in por_etapa],
        postulaciones_por_origen=[OrigenCount(origen=o, total=t) for o, t in por_origen],
        entrevistas_pendientes=entrevistas_pendientes,
    )
