"""Vacantes: las condiciones de un puesto en circulación, y sus convocatorias.

Lo que es de una ronda —fecha límite, estado, post, enlace, postulantes— ya no está
aquí: vive en `/convocatorias`. Aquí queda crear y editar las condiciones, activar o
desactivar la vacante, y abrir una convocatoria nueva.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.utils import slugify
from app.models.cargo import Cargo
from app.models.convocatoria import Convocatoria
from app.models.tipo_contrato import TipoContrato
from app.models.usuario import Usuario
from app.models.vacante import Vacante
from app.schemas.convocatoria import ConvocatoriaCreate, ConvocatoriaOut, VistaPreviaDelPost
from app.schemas.vacante import ImagenSubidaOut, VacanteCreate, VacanteOut
from app.services import almacenamiento_service, post_service
from app.api.v1 import convocatorias as convocatorias_api

router = APIRouter()


# ------------------------------------------------------------------ Helpers


def _con_relaciones(query):
    return query.options(
        selectinload(Vacante.tipo_contrato),
        selectinload(Vacante.cargo),
        selectinload(Vacante.convocatorias),
    )


def _a_salida(db: Session, vacante: Vacante, request: Request | None = None) -> VacanteOut:
    salida = VacanteOut.model_validate(vacante)
    salida.tipo_contrato_nombre = vacante.tipo_contrato.nombre if vacante.tipo_contrato else None
    salida.convocatorias = [convocatorias_api.a_salida(db, c, request) for c in vacante.convocatorias]
    salida.convocatoria_actual = salida.convocatorias[0] if salida.convocatorias else None
    return salida


def _vacante_o_404(db: Session, vacante_id: UUID) -> Vacante:
    vacante = db.scalar(_con_relaciones(select(Vacante)).where(Vacante.id == vacante_id))
    if vacante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")
    return vacante


def _validar_referencias(db: Session, payload: VacanteCreate) -> Cargo:
    cargo = db.get(Cargo, payload.cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cargo seleccionado no existe")
    if not cargo.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El cargo '{cargo.nombre}' está desactivado: actívalo antes de abrir una vacante",
        )
    if payload.tipo_contrato_id is not None and db.get(TipoContrato, payload.tipo_contrato_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El tipo de contrato seleccionado no existe"
        )
    return cargo


def _aplicar(vacante: Vacante, payload: VacanteCreate) -> None:
    datos = payload.model_dump(exclude={"primera_convocatoria"})
    datos["campos_personalizados"] = [c.model_dump() for c in payload.campos_personalizados]
    datos["destinatarios_internos"] = [str(c) for c in payload.destinatarios_internos]
    for campo, valor in datos.items():
        setattr(vacante, campo, valor)


def _nueva_convocatoria(vacante: Vacante, payload: ConvocatoriaCreate, creado_por: UUID) -> Convocatoria:
    """Arma la siguiente convocatoria de la vacante.

    El número es el siguiente al mayor que exista. Los campos del post que vengan
    vacíos se **heredan** de la convocatoria anterior: es lo que pidió el dueño, «con
    los mismos datos que ya se crearon». La fecha límite no se hereda: una ronda nueva
    tiene su propio cierre.
    """
    anterior = vacante.convocatoria_actual
    numero = (anterior.numero + 1) if anterior else 1
    datos = payload.model_dump()
    if anterior is not None:
        for campo in ("asunto", "post_cuerpo", "post_imagen_url"):
            if datos.get(campo) is None:
                datos[campo] = getattr(anterior, campo)
    # Cada convocatoria tiene su propio slug: hace falta saber a cuál se postuló alguien.
    return Convocatoria(
        vacante_id=vacante.id, numero=numero, slug=slugify(vacante.titulo), creado_por=creado_por, **datos
    )


# ------------------------------------------------------------ Las vacantes


@router.get("", response_model=list[VacanteOut])
def listar_vacantes(
    request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> list[VacanteOut]:
    vacantes = db.scalars(_con_relaciones(select(Vacante)).order_by(Vacante.creado_en.desc())).all()
    return [_a_salida(db, v, request) for v in vacantes]


@router.post("", response_model=VacanteOut, status_code=status.HTTP_201_CREATED)
def crear_vacante(
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Crea la vacante **y su convocatoria 1**: «Nueva vacante» sigue siendo un paso."""
    if payload.primera_convocatoria is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Una vacante nace con su primera convocatoria: falta `primera_convocatoria`",
        )
    cargo = _validar_referencias(db, payload)

    vacante = Vacante(titulo=cargo.nombre, empleador_id=current_user.id)
    _aplicar(vacante, payload)
    db.add(vacante)
    db.flush()
    db.add(_nueva_convocatoria(vacante, payload.primera_convocatoria, current_user.id))
    db.commit()
    return _a_salida(db, _vacante_o_404(db, vacante.id), request)


@router.put("/{vacante_id}", response_model=VacanteOut)
def actualizar_vacante(
    vacante_id: UUID,
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Actualiza las condiciones. `primera_convocatoria` se ignora: el ciclo va por `/convocatorias`."""
    vacante = _vacante_o_404(db, vacante_id)
    _validar_referencias(db, payload)
    _aplicar(vacante, payload)
    db.commit()
    return _a_salida(db, _vacante_o_404(db, vacante_id), request)


@router.patch("/{vacante_id}/toggle-activa", response_model=VacanteOut)
def alternar_activa(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Se desactiva, no se borra: tiene convocatorias y postulantes detrás."""
    vacante = _vacante_o_404(db, vacante_id)
    vacante.activa = not vacante.activa
    db.commit()
    return _a_salida(db, _vacante_o_404(db, vacante_id), request)


# -------------------------------------------------------- Las convocatorias


@router.post("/{vacante_id}/convocatorias", response_model=ConvocatoriaOut, status_code=status.HTTP_201_CREATED)
def abrir_convocatoria(
    vacante_id: UUID,
    payload: ConvocatoriaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ConvocatoriaOut:
    """Vuelve a convocar la vacante. La anterior se cierra si seguía abierta.

    Dos convocatorias abiertas a la vez de la misma vacante serían dos enlaces
    recibiendo gente para lo mismo, y nadie sabría a cuál mirar.
    """
    vacante = _vacante_o_404(db, vacante_id)
    if not vacante.activa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="La vacante está desactivada: actívala antes de convocar"
        )
    anterior = vacante.convocatoria_actual
    if anterior is not None and anterior.estado == "abierta":
        anterior.estado = "cerrada"

    convocatoria = _nueva_convocatoria(vacante, payload, current_user.id)
    db.add(convocatoria)
    db.commit()
    return convocatorias_api.a_salida(db, convocatorias_api.convocatoria_o_404(db, convocatoria.id), request)


# --------------------------------------------------------------- Utilidades


@router.post("/vista-previa", response_model=VistaPreviaDelPost)
def vista_previa_sin_guardar(
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VistaPreviaDelPost:
    """La vista previa con lo que hay escrito en el formulario, sin guardar nada.

    Existe para poder ir viendo el post **mientras se arma**. La vacante y la
    convocatoria que se construyen aquí no entran en la sesión: se usan y se tiran.
    """
    cargo = db.get(Cargo, payload.cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")
    ciclo = payload.primera_convocatoria or ConvocatoriaCreate(fecha_limite=datetime.now(timezone.utc))

    vacante = Vacante(
        **payload.model_dump(exclude={"campos_personalizados", "destinatarios_internos", "primera_convocatoria"}),
        titulo=cargo.nombre,
        campos_personalizados=[c.model_dump() for c in payload.campos_personalizados],
        destinatarios_internos=[str(c) for c in payload.destinatarios_internos],
    )
    vacante.cargo = cargo
    vacante.tipo_contrato = db.get(TipoContrato, payload.tipo_contrato_id) if payload.tipo_contrato_id else None
    # Todavía no hay slug: lo pone el servidor al guardar. El enlace lo dice en vez de
    # inventarse uno que no va a existir.
    convocatoria = Convocatoria(numero=1, slug="(se-genera-al-guardar)", **ciclo.model_dump())
    convocatoria.vacante = vacante

    enlace = f"{post_service.origen_del_frontend(request)}/postular/{convocatoria.slug}"
    return post_service.armar_vista_previa(convocatoria, enlace, post_service.nombre_de_quien_publica(db, usuario))


@router.post("/imagen", response_model=ImagenSubidaOut)
async def subir_imagen_de_post(
    # El campo se llama `file` porque es lo que manda `apiUpload` del frontend, igual
    # que el resto de las subidas: FastAPI busca el campo por el nombre del parámetro.
    file: UploadFile = File(...),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ImagenSubidaOut:
    """Sube la imagen y devuelve su URL, que luego se guarda en la convocatoria."""
    return ImagenSubidaOut(url=await almacenamiento_service.guardar_imagen_de_post(file))
