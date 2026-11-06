from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluacion import Evaluacion


def promedio_puntaje(db: Session, postulacion_id) -> float | None:
    puntajes = db.scalars(select(Evaluacion.puntaje).where(Evaluacion.postulacion_id == postulacion_id)).all()
    valores = [float(p) for p in puntajes if p is not None]
    if not valores:
        return None
    return round(sum(valores) / len(valores), 2)
