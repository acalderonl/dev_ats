from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.cargo import Cargo
from app.models.catalogos_educacion import AreaAcademica, NivelEducacion, TituloAcademico
from app.models.clasificacion_cargo import ClasificacionCargo
from app.models.competencia import CargoCompetencia, Competencia
from app.models.nombre_cargo import NombreCargo
from app.models.pregunta_filtro import PreguntaFiltro
from app.models.usuario import Usuario
from app.schemas.cargo import (
    CargoCreate,
    CargoOut,
    CompetenciaDelCargoOut,
    PreguntaFiltroCreate,
    PreguntaFiltroOut,
)

router = APIRouter()


def _con_catalogos(query):
    """`CargoOut.nombre` y `.clasificacion` salen de las relaciones: se cargan de una vez."""
    return query.options(
        selectinload(Cargo.nombre_catalogo),
        selectinload(Cargo.clasificacion_catalogo),
        selectinload(Cargo.nivel_educacion),
        selectinload(Cargo.titulo),
        selectinload(Cargo.area_academica),
        selectinload(Cargo.competencias).selectinload(CargoCompetencia.competencia),
    )


def _a_salida(cargo: Cargo) -> CargoOut:
    """Aplana las competencias del cargo: la UI necesita el nombre y el tipo, no solo el id."""
    return CargoOut(
        id=cargo.id,
        nombre_id=cargo.nombre_id,
        nombre=cargo.nombre,
        tiene_personal_a_cargo=cargo.tiene_personal_a_cargo,
        clasificacion_id=cargo.clasificacion_id,
        clasificacion=cargo.clasificacion,
        mision=cargo.mision,
        actividades=cargo.actividades,
        nivel_educacion_id=cargo.nivel_educacion_id,
        nivel_educacion=cargo.nivel_educacion.nombre if cargo.nivel_educacion else None,
        estado_educacion=cargo.estado_educacion,
        titulo_id=cargo.titulo_id,
        titulo=cargo.titulo.nombre if cargo.titulo else None,
        area_academica_id=cargo.area_academica_id,
        area_academica=cargo.area_academica.nombre if cargo.area_academica else None,
        experiencia_requerida=cargo.experiencia_requerida,
        activo=cargo.activo,
        competencias=[
            CompetenciaDelCargoOut(
                competencia_id=cc.competencia_id,
                requerido=cc.requerido,
                deseado=cc.deseado,
                nombre=cc.competencia.nombre,
                tipo=cc.competencia.tipo,
            )
            for cc in cargo.competencias
        ],
    )


def _cargo_completo(db: Session, cargo_id: int) -> Cargo:
    cargo = db.scalar(_con_catalogos(select(Cargo)).where(Cargo.id == cargo_id))
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
    return cargo


@router.get("", response_model=list[CargoOut])
def listar_cargos(db: Session = Depends(get_db)) -> list[CargoOut]:
    cargos = db.scalars(_con_catalogos(select(Cargo)).order_by(Cargo.id)).all()
    return [_a_salida(c) for c in cargos]


def _validar_catalogos(db: Session, payload: CargoCreate) -> None:
    """Un id que no existe en su catálogo rompería la clave foránea con un error feo."""
    if db.get(NombreCargo, payload.nombre_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de cargo seleccionado no existe en el catálogo",
        )
    if payload.clasificacion_id is not None and db.get(ClasificacionCargo, payload.clasificacion_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clasificación seleccionada no existe en el catálogo",
        )
    for modelo, valor, etiqueta in (
        (NivelEducacion, payload.nivel_educacion_id, "nivel de educación"),
        (TituloAcademico, payload.titulo_id, "título"),
        (AreaAcademica, payload.area_academica_id, "área académica"),
    ):
        if valor is not None and db.get(modelo, valor) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El {etiqueta} seleccionado no existe en el catálogo",
            )


def _guardar_competencias(db: Session, cargo_id: int, pedidas: list[dict]) -> None:
    """Reemplaza las competencias del cargo por las que vienen en la petición."""
    db.query(CargoCompetencia).filter(CargoCompetencia.cargo_id == cargo_id).delete()
    for item in pedidas:
        if db.get(Competencia, item["competencia_id"]) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La competencia {item['competencia_id']} no existe",
            )
        db.add(CargoCompetencia(cargo_id=cargo_id, **item))


@router.post("", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
def crear_cargo(
    payload: CargoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    _validar_catalogos(db, payload)

    datos = payload.model_dump()
    competencias_pedidas = datos.pop("competencias")

    cargo = Cargo(**datos)
    db.add(cargo)
    db.flush()
    _guardar_competencias(db, cargo.id, competencias_pedidas)

    db.commit()
    return _a_salida(_cargo_completo(db, cargo.id))


@router.put("/{cargo_id}", response_model=CargoOut)
def actualizar_cargo(
    cargo_id: int,
    payload: CargoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    """Reemplaza el contenido del cargo. `activo` no se toca aquí: eso va por toggle-activo."""
    cargo = _cargo_completo(db, cargo_id)
    _validar_catalogos(db, payload)

    datos = payload.model_dump()
    competencias_pedidas = datos.pop("competencias")
    for campo, valor in datos.items():
        setattr(cargo, campo, valor)

    _guardar_competencias(db, cargo_id, competencias_pedidas)

    db.commit()
    return _a_salida(_cargo_completo(db, cargo_id))


@router.patch("/{cargo_id}/toggle-activo", response_model=CargoOut)
def alternar_estado_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    cargo = _cargo_completo(db, cargo_id)
    cargo.activo = not cargo.activo
    db.commit()
    return _a_salida(_cargo_completo(db, cargo_id))


@router.get("/{cargo_id}/preguntas-filtro", response_model=list[PreguntaFiltroOut])
def listar_preguntas(cargo_id: int, db: Session = Depends(get_db)) -> list[PreguntaFiltroOut]:
    _cargo_completo(db, cargo_id)
    return db.scalars(select(PreguntaFiltro).where(PreguntaFiltro.cargo_id == cargo_id)).all()


@router.post("/{cargo_id}/preguntas-filtro", response_model=PreguntaFiltroOut, status_code=status.HTTP_201_CREATED)
def crear_pregunta(
    cargo_id: int,
    payload: PreguntaFiltroCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> PreguntaFiltroOut:
    _cargo_completo(db, cargo_id)

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
