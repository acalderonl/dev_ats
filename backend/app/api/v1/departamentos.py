"""Departamentos: la unidad organizativa de los cargos.

Se desactivan, no se borran, como todo lo que tiene historia detrás: un departamento con
cargos no puede desaparecer sin dejar a esos cargos sin sitio. Al desactivar uno, sus
cargos pasan a «Sin asignar», que existe para eso y por eso no se puede desactivar.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.cargo import Cargo
from app.models.departamento import Departamento
from app.models.usuario import Usuario
from app.schemas.departamento import DepartamentoCreate, DepartamentoOut

router = APIRouter()

SIN_ASIGNAR = "Sin asignar"


def _con_conteo(db: Session, departamento: Departamento) -> DepartamentoOut:
    cargos = db.scalar(select(func.count()).select_from(Cargo).where(Cargo.departamento_id == departamento.id)) or 0
    return DepartamentoOut(
        id=departamento.id,
        nombre=departamento.nombre,
        descripcion=departamento.descripcion,
        activo=departamento.activo,
        es_sistema=departamento.es_sistema,
        cargos=cargos,
    )


def _o_404(db: Session, departamento_id: int) -> Departamento:
    departamento = db.get(Departamento, departamento_id)
    if departamento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departamento no encontrado")
    return departamento


def sin_asignar(db: Session) -> Departamento:
    """El departamento de respaldo. Lo crea la migración; si falta, algo grave pasó."""
    departamento = db.scalar(select(Departamento).where(Departamento.es_sistema.is_(True)))
    if departamento is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falta el departamento «Sin asignar». Revisa las migraciones.",
        )
    return departamento


@router.get("", response_model=list[DepartamentoOut])
def listar_departamentos(db: Session = Depends(get_db)) -> list[DepartamentoOut]:
    """Todos, activos e inactivos: la pantalla los separa. «Sin asignar» va al final."""
    departamentos = db.scalars(select(Departamento).order_by(Departamento.es_sistema, Departamento.nombre)).all()
    return [_con_conteo(db, d) for d in departamentos]


@router.post("", response_model=DepartamentoOut, status_code=status.HTTP_201_CREATED)
def crear_departamento(
    payload: DepartamentoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> DepartamentoOut:
    if db.scalar(select(Departamento).where(func.lower(Departamento.nombre) == payload.nombre.lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un departamento con ese nombre")
    departamento = Departamento(nombre=payload.nombre, descripcion=payload.descripcion)
    db.add(departamento)
    db.commit()
    return _con_conteo(db, departamento)


@router.put("/{departamento_id}", response_model=DepartamentoOut)
def actualizar_departamento(
    departamento_id: int,
    payload: DepartamentoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> DepartamentoOut:
    departamento = _o_404(db, departamento_id)
    if departamento.es_sistema and payload.nombre != departamento.nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="«Sin asignar» no se renombra: el sistema lo busca por ese nombre.",
        )
    repetido = db.scalar(
        select(Departamento).where(
            func.lower(Departamento.nombre) == payload.nombre.lower(), Departamento.id != departamento_id
        )
    )
    if repetido:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un departamento con ese nombre")
    departamento.nombre = payload.nombre
    departamento.descripcion = payload.descripcion
    db.commit()
    return _con_conteo(db, departamento)


@router.patch("/{departamento_id}/toggle-activo", response_model=DepartamentoOut)
def alternar_estado_departamento(
    departamento_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> DepartamentoOut:
    """Desactiva o reactiva. Al desactivar, sus cargos pasan a «Sin asignar».

    Se mueven de verdad y no solo se esconden: un cargo tiene que tener siempre un
    departamento al que pertenecer, y uno desactivado ya no cuenta como tal.
    """
    departamento = _o_404(db, departamento_id)
    if departamento.es_sistema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="«Sin asignar» no se desactiva: es donde caen los cargos de los departamentos que se desactivan.",
        )

    if departamento.activo:
        respaldo = sin_asignar(db)
        db.query(Cargo).filter(Cargo.departamento_id == departamento.id).update(
            {Cargo.departamento_id: respaldo.id}, synchronize_session=False
        )
    departamento.activo = not departamento.activo
    db.commit()
    return _con_conteo(db, departamento)
