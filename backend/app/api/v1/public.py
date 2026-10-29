from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limites import limitar
from app.models.pregunta_filtro import PreguntaFiltro
from app.models.postulacion import Postulacion
from app.models.postulante import Postulante
from app.models.postulante_perfil import PostulanteEducacion, PostulanteExperiencia, PostulanteIdioma
from app.models.vacante import Vacante
from app.schemas.cargo import PreguntaFiltroOut
from app.schemas.postulante import ArchivoSubido, CvParseadoOut, PostularRequest, PostulanteOut
from app.schemas.cv_extraido import CvExtraidoOut
from app.schemas.vacante import VacantePublicaOut
from app.services import almacenamiento_service, extraccion_cv_service
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


@router.get(
    "/vacantes/{slug}",
    response_model=VacantePublicaOut,
    dependencies=[Depends(limitar("consulta"))],
)
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


@router.post(
    "/parse-cv",
    response_model=CvParseadoOut,
    dependencies=[Depends(limitar("leer_cv"))],
)
async def parsear_cv(file: UploadFile = File(...)) -> CvParseadoOut:
    """Extracción básica. Se mantiene para no romper a quien ya la use."""
    return await parse_cv_upload(file)


@router.post(
    "/leer-cv",
    response_model=CvExtraidoOut,
    dependencies=[Depends(limitar("leer_cv"))],
)
async def leer_cv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> CvExtraidoOut:
    """Guarda el CV y devuelve los campos del formulario de postulación.

    Sin autenticación porque la usa el candidato antes de existir en el sistema. El
    tope de tamaño y de formato lo aplica el propio servicio.

    Se guarda en la misma subida: pedir el archivo dos veces —una para entenderlo y
    otra para conservarlo— haría al candidato subirlo dos veces, y la segunda cuesta
    otra llamada de pago.

    Se lee **antes** de guardar. Al revés, un archivo que el lector rechaza (un `.doc`
    antiguo, uno que pasa del tamaño) ya habría dejado su copia en el volumen sin que
    ninguna ficha llegue nunca a apuntar a ella.
    """
    extraido = await extraccion_cv_service.leer_cv(db, file)
    await file.seek(0)
    extraido.cv_documento_url = await almacenamiento_service.guardar_cv(file)
    return extraido


@router.post(
    "/foto",
    response_model=ArchivoSubido,
    dependencies=[Depends(limitar("subir_archivo"))],
)
async def subir_foto(file: UploadFile = File(...)) -> ArchivoSubido:
    """Guarda la foto del candidato.

    La URL que devuelve **no se abre sin sesión**: la foto es un dato personal y vive
    en la carpeta privada. El candidato ve la suya del archivo que acaba de elegir,
    sin pedirla de vuelta.
    """
    return ArchivoSubido(url=await almacenamiento_service.guardar_foto_de_candidato(file))


def _nivel_mas_alto(educacion: list) -> str | None:
    """El nivel de estudios más alto de la lista, para el filtro de contactos.

    Es un resumen denormalizado: la verdad está en `postulante_educacion`. Se calcula
    al crear la ficha porque el directorio filtra por él en cada búsqueda y bajar a la
    tabla cada vez saldría más caro que mantener esta copia.
    """
    orden = ["Secundaria", "Técnico", "Universitario", "Máster", "Posgrado", "Doctorado"]
    niveles = [e.nivel_estudio for e in educacion if e.nivel_estudio]
    if not niveles:
        return None
    conocidos = [n for n in niveles if n in orden]
    return max(conocidos, key=orden.index) if conocidos else niveles[0]


def _crear_postulante(payload: PostularRequest) -> Postulante:
    """Arma la ficha con sus tres listas. El orden de cada lista es el que llegó."""
    postulante = Postulante(
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        cedula=payload.cedula,
        email=payload.email,
        tipo_documento=payload.tipo_documento,
        fecha_nacimiento=payload.fecha_nacimiento,
        genero=payload.genero,
        nacionalidad=payload.nacionalidad,
        foto_url=payload.foto_url,
        telefono_codigo_pais=payload.telefono_codigo_pais,
        telefono=payload.telefono,
        telefono_tipo=payload.telefono_tipo,
        pais_residencia=payload.pais_residencia,
        provincia=payload.provincia,
        localidad=payload.localidad,
        nivel_instruccion=payload.nivel_instruccion or _nivel_mas_alto(payload.educacion),
        estudios_secundarios_completos=payload.estudios_secundarios_completos,
        linkedin_url=payload.linkedin_url,
        otras_redes=[r.model_dump() for r in payload.otras_redes],
        expectativas=payload.expectativas,
        cv_documento_url=payload.cv_documento_url,
        edad=payload.edad,
        origen_datos=payload.origen_datos,
        # Se guarda cuándo, no solo que sí: sin la fecha no se puede demostrar qué
        # versión de la política aceptó.
        acepto_privacidad_en=datetime.now(timezone.utc),
    )
    postulante.educacion = [PostulanteEducacion(orden=i, **e.model_dump()) for i, e in enumerate(payload.educacion)]
    postulante.idiomas = [PostulanteIdioma(orden=i, **i_.model_dump()) for i, i_ in enumerate(payload.idiomas)]
    postulante.experiencia = [
        PostulanteExperiencia(orden=i, **e.model_dump()) for i, e in enumerate(payload.experiencia)
    ]
    return postulante


@router.post(
    "/vacantes/{slug}/postular",
    response_model=PostulanteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limitar("postular"))],
)
def postular(slug: str, payload: PostularRequest, db: Session = Depends(get_db)) -> PostulanteOut:
    vacante = _get_vacante_activa_or_410(db, slug)

    postulante = db.scalar(select(Postulante).where(Postulante.cedula == payload.cedula))
    if postulante is None:
        postulante = _crear_postulante(payload)
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
