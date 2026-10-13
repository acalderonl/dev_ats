"""CRUD de los catálogos que alimentan los selectores del formulario de cargo.

Un solo router sirve a los dos catálogos (y a los que vengan): la tabla de cada uno es
propia —así la base garantiza las claves foráneas— pero las operaciones son idénticas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.cargo import Cargo
from app.models.cargo_educacion import CargoAreaAcademica, CargoNivelEducacion, CargoTitulo
from app.models.catalogos_educacion import AreaAcademica, NivelEducacion, TituloAcademico
from app.models.clasificacion_cargo import ClasificacionCargo
from app.models.nombre_cargo import NombreCargo
from app.models.usuario import Usuario
from app.schemas.catalogo import CatalogoCreate, CatalogoOut, CatalogoUpdate

router = APIRouter()

# catálogo -> (modelo del catálogo, columna que lo referencia).
# Unos los referencia `cargos` directamente; los de educación, su tabla puente, porque
# desde la migración 0005 un cargo admite hasta dos de cada uno.
CATALOGOS = {
    "nombres-cargo": (NombreCargo, Cargo.nombre_id),
    "clasificaciones": (ClasificacionCargo, Cargo.clasificacion_id),
    "niveles-educacion": (NivelEducacion, CargoNivelEducacion.nivel_id),
    "titulos": (TituloAcademico, CargoTitulo.titulo_id),
    "areas-academicas": (AreaAcademica, CargoAreaAcademica.area_id),
}


def _resolver(catalogo: str):
    entrada = CATALOGOS.get(catalogo)
    if entrada is None:
        disponibles = ", ".join(CATALOGOS)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catálogo '{catalogo}' no existe. Disponibles: {disponibles}",
        )
    return entrada


def _obtener_item(db: Session, modelo, item_id: int):
    item = db.get(modelo, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento no encontrado")
    return item


def _conteo_de_uso(db: Session, columna, item_id: int) -> int:
    """Cuántas veces se usa. La tabla sale de la propia columna, sea `cargos` o una puente."""
    tabla = columna.parent.class_
    return db.scalar(select(func.count()).select_from(tabla).where(columna == item_id)) or 0


@router.get("/{catalogo}", response_model=list[CatalogoOut])
def listar(
    catalogo: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[CatalogoOut]:
    modelo, columna = _resolver(catalogo)
    items = db.scalars(select(modelo).order_by(modelo.nombre)).all()
    return [
        CatalogoOut(id=i.id, nombre=i.nombre, activo=i.activo, en_uso=_conteo_de_uso(db, columna, i.id) > 0)
        for i in items
    ]


@router.post("/{catalogo}", response_model=CatalogoOut, status_code=status.HTTP_201_CREATED)
def crear(
    catalogo: str,
    payload: CatalogoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CatalogoOut:
    modelo, _columna = _resolver(catalogo)
    item = modelo(nombre=payload.nombre)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un elemento con el nombre '{payload.nombre}'",
        ) from exc
    db.refresh(item)
    return CatalogoOut(id=item.id, nombre=item.nombre, activo=item.activo, en_uso=False)


@router.put("/{catalogo}/{item_id}", response_model=CatalogoOut)
def actualizar(
    catalogo: str,
    item_id: int,
    payload: CatalogoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CatalogoOut:
    modelo, columna = _resolver(catalogo)
    item = _obtener_item(db, modelo, item_id)

    if payload.nombre is not None:
        item.nombre = payload.nombre
    if payload.activo is not None:
        item.activo = payload.activo

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un elemento con el nombre '{payload.nombre}'",
        ) from exc
    db.refresh(item)
    return CatalogoOut(
        id=item.id,
        nombre=item.nombre,
        activo=item.activo,
        en_uso=_conteo_de_uso(db, columna, item.id) > 0,
    )


@router.delete("/{catalogo}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    catalogo: str,
    item_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> None:
    modelo, columna = _resolver(catalogo)
    item = _obtener_item(db, modelo, item_id)

    en_uso = _conteo_de_uso(db, columna, item_id)
    if en_uso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede eliminar '{item.nombre}': lo usan {en_uso} cargo(s). "
                "Desactívalo si ya no quieres que aparezca en el selector."
            ),
        )

    db.delete(item)
    db.commit()
