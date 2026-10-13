from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.pregunta_filtro import PreguntaFiltro
from app.models.postulacion import Postulacion
from app.models.postulante import Postulante
from app.models.vacante import Vacante
from app.schemas.cargo import PreguntaFiltroOut
from app.schemas.postulante import CvParseadoOut, PostularRequest, PostulanteOut
from app.schemas.vacante import VacantePublicaOut
from app.services.cv_parser_service import parse_cv_upload

router = APIRouter()


def _get_vacante_activa_or_410(db: Session, slug: str) -> Vacante:
    vacante = db.scalar(select(Vacante).where(Vacante.slug == slug))
    if vacante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")

    fecha_limite = vacante.fecha_limite
    if fecha_limite.tzinfo is None:
        fecha_limite = fecha_limite.replace(tzinfo=timezone.utc)

    if vacante.estado != "abierta" or fecha_limite < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Esta vacante ha expirado. Revisa nuestro LinkedIn para más información.",
        )
    # Una vacante interna no existe para el portal público, aunque esté abierta y
    # alguien tenga el enlace: para eso se marcó interna.
    if vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacante no encontrada",
        )
    return vacante


@router.get("/vacantes/{slug}", response_model=VacantePublicaOut)
def obtener_vacante_publica(slug: str, db: Session = Depends(get_db)) -> VacantePublicaOut:
    vacante = _get_vacante_activa_or_410(db, slug)
    preguntas = db.scalars(select(PreguntaFiltro).where(PreguntaFiltro.cargo_id == vacante.cargo_id)).all()
    return VacantePublicaOut(
        id=vacante.id,
        titulo=vacante.titulo,
        descripcion=vacante.descripcion,
        slug=vacante.slug,
        fecha_limite=vacante.fecha_limite,
        cargo_nombre=vacante.cargo.nombre,
        remuneracion=vacante.remuneracion,
        hora_entrada=vacante.hora_entrada,
        hora_salida=vacante.hora_salida,
        tipo_contrato=vacante.tipo_contrato.nombre if vacante.tipo_contrato else None,
        campos_personalizados=vacante.campos_personalizados or [],
        preguntas_filtro=[PreguntaFiltroOut.model_validate(p) for p in preguntas],
    )


@router.post("/parse-cv", response_model=CvParseadoOut)
async def parsear_cv(file: UploadFile = File(...)) -> CvParseadoOut:
    return await parse_cv_upload(file)


@router.post("/vacantes/{slug}/postular", response_model=PostulanteOut, status_code=status.HTTP_201_CREATED)
def postular(slug: str, payload: PostularRequest, db: Session = Depends(get_db)) -> PostulanteOut:
    vacante = _get_vacante_activa_or_410(db, slug)

    postulante = db.scalar(select(Postulante).where(Postulante.cedula == payload.cedula))
    if postulante is None:
        postulante = Postulante(
            nombres=payload.nombres,
            apellidos=payload.apellidos,
            cedula=payload.cedula,
            email=payload.email,
            telefono=payload.telefono,
            edad=payload.edad,
            formacion_secundaria=payload.formacion_secundaria.model_dump() if payload.formacion_secundaria else None,
            formacion_superior=payload.formacion_superior.model_dump() if payload.formacion_superior else None,
            nivel_instruccion=payload.nivel_instruccion,
            titulos=payload.titulos,
            experiencia_laboral=[e.model_dump() for e in payload.experiencia_laboral],
            cv_documento_url="pendiente-de-almacenamiento",
        )
        db.add(postulante)
        db.flush()

    postulacion = Postulacion(
        vacante_id=vacante.id,
        postulante_id=postulante.id,
        respuestas_filtro=payload.respuestas_filtro,
        estado_pipeline="pendiente_autorizacion",
        origen=payload.origen,
    )
    db.add(postulacion)
    db.commit()
    db.refresh(postulante)
    return postulante
