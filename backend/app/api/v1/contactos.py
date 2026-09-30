from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.postulacion import Postulacion
from app.models.postulante import Postulante
from app.models.usuario import Usuario
from app.models.vacante import Vacante
from app.schemas.postulante import ContactoOut, PostulanteOut

router = APIRouter()


@router.get("", response_model=list[ContactoOut])
def listar_contactos(
    q: str | None = None,
    nivel_instruccion: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[ContactoOut]:
    query = select(Postulante)
    if q:
        like = f"%{q}%"
        nombre_completo = Postulante.nombres + " " + Postulante.apellidos
        query = query.where(
            or_(
                Postulante.nombres.ilike(like),
                Postulante.apellidos.ilike(like),
                nombre_completo.ilike(like),
                Postulante.cedula.ilike(like),
                Postulante.email.ilike(like),
            )
        )
    if nivel_instruccion:
        query = query.where(Postulante.nivel_instruccion == nivel_instruccion)

    postulantes = db.scalars(query.order_by(Postulante.creado_en.desc())).all()
    postulante_ids = [p.id for p in postulantes]

    postulaciones = db.scalars(
        select(Postulacion)
        .where(Postulacion.postulante_id.in_(postulante_ids))
        .order_by(Postulacion.creado_en.asc())
    ).all()

    por_postulante: dict = defaultdict(list)
    for pos in postulaciones:
        por_postulante[pos.postulante_id].append(pos)

    vacante_ids = {pos.vacante_id for pos in postulaciones}
    vacantes_por_id = {v.id: v for v in db.scalars(select(Vacante).where(Vacante.id.in_(vacante_ids))).all()}

    resultado: list[ContactoOut] = []
    for postulante in postulantes:
        historial = por_postulante.get(postulante.id, [])
        ultima = historial[-1] if historial else None
        base = PostulanteOut.model_validate(postulante)
        resultado.append(
            ContactoOut(
                **base.model_dump(),
                ultimo_estado_pipeline=ultima.estado_pipeline if ultima else None,
                ultima_vacante=vacantes_por_id[ultima.vacante_id].titulo if ultima else None,
                total_postulaciones=len(historial),
            )
        )
    return resultado
