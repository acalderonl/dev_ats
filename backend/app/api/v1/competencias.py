"""Catálogo de conocimientos académicos y habilidades blandas.

El problema que resuelve: si cada cargo escribe sus competencias a mano, acaban conviviendo
"Trabajo en equipo", "trabajo en equipo" y "Trabajo en Equipo" como tres cosas distintas.
Aquí se guarda una sola vez y se comparten entre cargos.

Dos defensas contra el duplicado:
1. `nombre_normalizado` (sin tildes, minúsculas) es único por tipo: los que solo cambian en
   mayúsculas o acentos ni siquiera se pueden crear.
2. La búsqueda devuelve además los PARECIDOS, usando trigramas de PostgreSQL, para que quien
   escribe vea "Trabajo en equipo" antes de crear "Trabajo en equipos".
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.utils import normalizar
from app.models.competencia import CargoCompetencia, Competencia
from app.models.usuario import Usuario
from app.schemas.competencia import CompetenciaCreate, CompetenciaOut

router = APIRouter()

# Por debajo de esto dos textos ya no se parecen en nada útil.
UMBRAL_PARECIDO = 0.3


def _conteo_de_usos(db: Session, competencia_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(CargoCompetencia).where(CargoCompetencia.competencia_id == competencia_id)
        )
        or 0
    )


@router.get("", response_model=list[CompetenciaOut])
def buscar(
    tipo: str = Query(..., pattern="^(academico|blanda)$"),
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[CompetenciaOut]:
    """Lista las competencias de un tipo; con `q`, las que contienen o se parecen al texto."""
    consulta = select(Competencia).where(Competencia.tipo == tipo)

    if q and q.strip():
        objetivo = normalizar(q)
        parecido = func.similarity(Competencia.nombre_normalizado, objetivo)
        consulta = (
            select(Competencia, parecido.label("similitud"))
            .where(Competencia.tipo == tipo)
            .where(
                or_(
                    Competencia.nombre_normalizado.contains(objetivo),
                    parecido > UMBRAL_PARECIDO,
                )
            )
            .order_by(
                # Primero lo que contiene literalmente lo escrito, luego por parecido.
                Competencia.nombre_normalizado.contains(objetivo).desc(),
                parecido.desc(),
            )
            .limit(10)
        )
        filas = db.execute(consulta).all()
        return [
            CompetenciaOut(
                id=c.id,
                nombre=c.nombre,
                tipo=c.tipo,
                activo=c.activo,
                usos=_conteo_de_usos(db, c.id),
                similitud=round(float(similitud), 2),
            )
            for c, similitud in filas
        ]

    competencias = db.scalars(consulta.order_by(Competencia.nombre).limit(50)).all()
    return [
        CompetenciaOut(id=c.id, nombre=c.nombre, tipo=c.tipo, activo=c.activo, usos=_conteo_de_usos(db, c.id))
        for c in competencias
    ]


@router.post("", response_model=CompetenciaOut, status_code=status.HTTP_201_CREATED)
def crear(
    payload: CompetenciaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CompetenciaOut:
    normalizado = normalizar(payload.nombre)

    existente = db.scalar(
        select(Competencia).where(Competencia.tipo == payload.tipo, Competencia.nombre_normalizado == normalizado)
    )
    if existente is not None:
        # No es un error: es la misma competencia escrita de otra forma. Se devuelve la que
        # ya existe para que el cargo la reutilice en vez de crear un duplicado.
        return CompetenciaOut(
            id=existente.id,
            nombre=existente.nombre,
            tipo=existente.tipo,
            activo=existente.activo,
            usos=_conteo_de_usos(db, existente.id),
            similitud=1.0,
        )

    competencia = Competencia(nombre=payload.nombre, nombre_normalizado=normalizado, tipo=payload.tipo)
    db.add(competencia)
    db.commit()
    db.refresh(competencia)
    return CompetenciaOut(
        id=competencia.id,
        nombre=competencia.nombre,
        tipo=competencia.tipo,
        activo=competencia.activo,
        usos=0,
    )


@router.delete("/{competencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    competencia_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> None:
    competencia = db.get(Competencia, competencia_id)
    if competencia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competencia no encontrada")

    usos = _conteo_de_usos(db, competencia_id)
    if usos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar '{competencia.nombre}': la usan {usos} cargo(s).",
        )

    db.delete(competencia)
    db.commit()
