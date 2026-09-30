from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.cargo import Cargo
from app.models.pregunta_filtro import PreguntaFiltro
from app.models.usuario import Usuario
from app.schemas.cargo import CargoCreate, CargoOut, PreguntaFiltroCreate, PreguntaFiltroOut

router = APIRouter()


@router.get("", response_model=list[CargoOut])
def listar_cargos(db: Session = Depends(get_db)) -> list[CargoOut]:
    return db.scalars(select(Cargo)).all()


@router.post("", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
def crear_cargo(
    payload: CargoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    cargo = Cargo(**payload.model_dump())
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    return cargo


@router.patch("/{cargo_id}/toggle-activo", response_model=CargoOut)
def alternar_estado_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    cargo = db.get(Cargo, cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
    cargo.activo = not cargo.activo
    db.commit()
    db.refresh(cargo)
    return cargo


@router.get("/{cargo_id}/preguntas-filtro", response_model=list[PreguntaFiltroOut])
def listar_preguntas(cargo_id: int, db: Session = Depends(get_db)) -> list[PreguntaFiltroOut]:
    cargo = db.get(Cargo, cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
    return db.scalars(select(PreguntaFiltro).where(PreguntaFiltro.cargo_id == cargo_id)).all()


@router.post("/{cargo_id}/preguntas-filtro", response_model=PreguntaFiltroOut, status_code=status.HTTP_201_CREATED)
def crear_pregunta(
    cargo_id: int,
    payload: PreguntaFiltroCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> PreguntaFiltroOut:
    cargo = db.get(Cargo, cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")

    pregunta = PreguntaFiltro(cargo_id=cargo_id, **payload.model_dump())
    db.add(pregunta)
    db.commit()
    db.refresh(pregunta)
    return pregunta


@router.delete("/preguntas-filtro/{pregunta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pregunta(
    pregunta_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> None:
    pregunta = db.get(PreguntaFiltro, pregunta_id)
    if pregunta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    db.delete(pregunta)
    db.commit()
