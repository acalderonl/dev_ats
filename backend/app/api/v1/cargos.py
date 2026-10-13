from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.cargo import Cargo
from app.models.cargo_educacion import CargoAreaAcademica, CargoNivelEducacion, CargoTitulo
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
    ItemDeEducacionOut,
    NivelDelCargoOut,
    PreguntaFiltroCreate,
    PreguntaFiltroOut,
)

router = APIRouter()


def _con_catalogos(query):
    """`CargoOut.nombre` y `.clasificacion` salen de las relaciones: se cargan de una vez."""
    return query.options(
        selectinload(Cargo.nombre_catalogo),
        selectinload(Cargo.clasificacion_catalogo),
        selectinload(Cargo.niveles_educacion).selectinload(CargoNivelEducacion.nivel),
        selectinload(Cargo.titulos).selectinload(CargoTitulo.titulo),
        selectinload(Cargo.areas_academicas).selectinload(CargoAreaAcademica.area),
        selectinload(Cargo.competencias).selectinload(CargoCompetencia.competencia),
    )


def _a_salida(cargo: Cargo) -> CargoOut:
    """Aplana las relaciones: la UI necesita el nombre además del id."""
    return CargoOut(
        id=cargo.id,
        nombre_id=cargo.nombre_id,
        nombre=cargo.nombre,
        tiene_personal_a_cargo=cargo.tiene_personal_a_cargo,
        clasificacion_id=cargo.clasificacion_id,
        clasificacion=cargo.clasificacion,
        mision=cargo.mision,
        actividades=cargo.actividades,
        niveles_educacion=[
            NivelDelCargoOut(nivel_id=n.nivel_id, estado=n.estado, nombre=n.nivel.nombre)
            for n in cargo.niveles_educacion
        ],
        titulos=[ItemDeEducacionOut(id=t.titulo_id, nombre=t.titulo.nombre) for t in cargo.titulos],
        areas_academicas=[ItemDeEducacionOut(id=a.area_id, nombre=a.area.nombre) for a in cargo.areas_academicas],
        experiencia_requerida=cargo.experiencia_requerida,
        experiencia_empresas_similares=cargo.experiencia_empresas_similares,
        experiencia_cargos_similares=cargo.experiencia_cargos_similares,
        experiencia_interna_otros_cargos=cargo.experiencia_interna_otros_cargos,
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
    for modelo, ids, etiqueta in (
        (NivelEducacion, [n.nivel_id for n in payload.niveles_educacion], "nivel de educación"),
        (TituloAcademico, payload.titulos_ids, "título"),
        (AreaAcademica, payload.areas_academicas_ids, "área académica"),
    ):
        for valor in ids:
            if db.get(modelo, valor) is None:
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


def _guardar_educacion(db: Session, cargo_id: int, payload: CargoCreate) -> None:
    """Reemplaza la educación formal del cargo. El orden de las listas es el que se muestra."""
    db.query(CargoNivelEducacion).filter(CargoNivelEducacion.cargo_id == cargo_id).delete()
    db.query(CargoTitulo).filter(CargoTitulo.cargo_id == cargo_id).delete()
    db.query(CargoAreaAcademica).filter(CargoAreaAcademica.cargo_id == cargo_id).delete()

    for orden, nivel in enumerate(payload.niveles_educacion):
        db.add(CargoNivelEducacion(cargo_id=cargo_id, nivel_id=nivel.nivel_id, estado=nivel.estado, orden=orden))
    for orden, titulo_id in enumerate(payload.titulos_ids):
        db.add(CargoTitulo(cargo_id=cargo_id, titulo_id=titulo_id, orden=orden))
    for orden, area_id in enumerate(payload.areas_academicas_ids):
        db.add(CargoAreaAcademica(cargo_id=cargo_id, area_id=area_id, orden=orden))


@router.post("", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
def crear_cargo(
    payload: CargoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> CargoOut:
    _validar_catalogos(db, payload)

    datos = payload.model_dump()
    competencias_pedidas = datos.pop("competencias")
    # Las listas de educación tienen su propia tabla: no son columnas de `cargos`.
    for campo in ("niveles_educacion", "titulos_ids", "areas_academicas_ids"):
        datos.pop(campo)

    cargo = Cargo(**datos)
    db.add(cargo)
    db.flush()
    _guardar_competencias(db, cargo.id, competencias_pedidas)
    _guardar_educacion(db, cargo.id, payload)

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
    for campo in ("niveles_educacion", "titulos_ids", "areas_academicas_ids"):
        datos.pop(campo)
    for campo, valor in datos.items():
        setattr(cargo, campo, valor)

    _guardar_competencias(db, cargo_id, competencias_pedidas)
    _guardar_educacion(db, cargo_id, payload)

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
