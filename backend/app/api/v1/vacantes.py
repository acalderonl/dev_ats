from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.utils import normalizar, slugify
from app.models.cargo import Cargo
from app.models.tipo_contrato import TipoContrato
from app.models.usuario import Usuario
from app.models.vacante import TokenLinkedIn, Vacante
from app.schemas.vacante import (
    CambioDeEstado,
    CambioDeEstadoDelPost,
    EnvioInternoOut,
    ImagenSubidaOut,
    ParaCompartirEnLinkedIn,
    ResultadoDePublicacion,
    VacanteCreate,
    VacanteOut,
    VistaPreviaDelPost,
    WhatsAppShareOut,
)
from app.services import almacenamiento_service, configuracion_service, correo_service, linkedin_service
from app.services import whatsapp_service

router = APIRouter()


def _origen_del_frontend(request: Request) -> str:
    return request.headers.get("origin") or get_settings().frontend_origin


def _url_publica(request: Request, vacante: Vacante) -> str:
    return f"{_origen_del_frontend(request)}/postular/{vacante.slug}"


def _a_salida(vacante: Vacante, request: Request | None = None) -> VacanteOut:
    salida = VacanteOut.model_validate(vacante)
    salida.tipo_contrato_nombre = vacante.tipo_contrato.nombre if vacante.tipo_contrato else None
    if request is not None:
        salida.url_publica = _url_publica(request, vacante)
    return salida


def _con_relaciones(query):
    return query.options(selectinload(Vacante.tipo_contrato), selectinload(Vacante.cargo))


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
    datos = payload.model_dump()
    datos["campos_personalizados"] = [c.model_dump() for c in payload.campos_personalizados]
    datos["destinatarios_internos"] = [str(c) for c in payload.destinatarios_internos]
    for campo, valor in datos.items():
        setattr(vacante, campo, valor)


@router.get("", response_model=list[VacanteOut])
def listar_vacantes(
    request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> list[VacanteOut]:
    vacantes = db.scalars(_con_relaciones(select(Vacante)).order_by(Vacante.creado_en.desc())).all()
    return [_a_salida(v, request) for v in vacantes]


@router.post("", response_model=VacanteOut, status_code=status.HTTP_201_CREATED)
def crear_vacante(
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    cargo = _validar_referencias(db, payload)

    vacante = Vacante(
        # El título se copia del cargo: de él sale el slug, que es la URL pública.
        titulo=cargo.nombre,
        slug=slugify(cargo.nombre),
        empleador_id=current_user.id,
    )
    _aplicar(vacante, payload)
    db.add(vacante)
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante.id), request)


@router.put("/{vacante_id}", response_model=VacanteOut)
def actualizar_vacante(
    vacante_id: UUID,
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Actualiza el contenido. El slug **no** se recalcula: ya está repartido."""
    vacante = _vacante_o_404(db, vacante_id)
    _validar_referencias(db, payload)
    _aplicar(vacante, payload)
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.patch("/{vacante_id}/estado", response_model=VacanteOut)
def cambiar_estado(
    vacante_id: UUID,
    payload: CambioDeEstado,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    vacante = _vacante_o_404(db, vacante_id)
    vacante.estado = payload.estado
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.patch("/{vacante_id}/post-estado", response_model=VacanteOut)
def cambiar_estado_del_post(
    vacante_id: UUID,
    payload: CambioDeEstadoDelPost,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VacanteOut:
    """Mover el post entre borrador y programado a mano.

    No sirve para marcarlo 'publicado': eso solo lo pone el publicador, porque si no
    la pantalla diría que salió algo que nunca salió.
    """
    vacante = _vacante_o_404(db, vacante_id)
    if payload.post_estado == "publicado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'publicado' no se pone a mano: resulta de publicar de verdad",
        )
    if payload.post_estado == "programado" and vacante.post_programado_para is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para programar el post hace falta una fecha y hora de publicación",
        )
    vacante.post_estado = payload.post_estado
    db.commit()
    return _a_salida(_vacante_o_404(db, vacante_id), request)


@router.post("/imagen", response_model=ImagenSubidaOut)
async def subir_imagen_de_post(
    # El campo se llama `file` porque es lo que manda `apiUpload` del frontend, igual
    # que el resto de las subidas. Se llamó `archivo` y devolvía 422 a todo el mundo:
    # FastAPI busca el campo por el nombre del parámetro.
    file: UploadFile = File(...),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ImagenSubidaOut:
    """Sube la imagen y devuelve su URL, que luego se guarda en la vacante."""
    return ImagenSubidaOut(url=await almacenamiento_service.guardar_imagen_de_post(file))


def _etiqueta(texto: str) -> str:
    """Convierte un nombre en una etiqueta de LinkedIn: `#AnalistaDeReclutamiento`.

    Sin tildes ni eñes a propósito: LinkedIn las admite, pero una etiqueta con tilde y
    otra sin ella son dos etiquetas distintas, y quien busca escribe la fácil.
    """
    limpio = normalizar(texto)
    return "#" + "".join(palabra.capitalize() for palabra in limpio.split() if palabra.isalnum())


def _etiquetas(vacante: Vacante) -> str:
    """Las etiquetas del post, sin repetir y sin las vacías."""
    candidatas = ["#Empleo", _etiqueta(vacante.titulo)]
    if vacante.cargo and vacante.cargo.clasificacion:
        candidatas.append(_etiqueta(vacante.cargo.clasificacion))

    vistas: list[str] = []
    for etiqueta in candidatas:
        if len(etiqueta) > 1 and etiqueta not in vistas:
            vistas.append(etiqueta)
    return " ".join(vistas)


def _texto_del_post(vacante: Vacante, enlace: str) -> str:
    partes = [vacante.asunto or vacante.titulo, "", vacante.post_cuerpo or vacante.descripcion]
    if vacante.remuneracion is not None:
        partes.append(f"Remuneración: ${vacante.remuneracion:,.2f}")
    if vacante.hora_entrada and vacante.hora_salida:
        partes.append(f"Horario: {vacante.hora_entrada:%H:%M} a {vacante.hora_salida:%H:%M}")
    if vacante.tipo_contrato:
        partes.append(f"Tipo de contrato: {vacante.tipo_contrato.nombre}")
    for campo in vacante.campos_personalizados or []:
        if campo.get("valor"):
            partes.append(f"{campo['etiqueta']}: {campo['valor']}")
    # La fecha de cierre mueve a postular hoy en vez de "luego lo miro".
    partes.append(f"Postulaciones hasta el {vacante.fecha_limite:%d/%m/%Y}")
    partes += ["", f"Postula aquí: {enlace}", "", _etiquetas(vacante)]
    return "\n".join(partes)


def _armar_vista_previa(vacante: Vacante, enlace: str, autor: str) -> VistaPreviaDelPost:
    """Lo que se verá, construido con las **mismas** piezas que se publican.

    Una pantalla que rehiciera el texto por su cuenta enseñaría algo parecido a lo que
    sale, y "parecido" no sirve para decidir si el post está listo.
    """
    texto = _texto_del_post(vacante, enlace)
    return VistaPreviaDelPost(
        asunto=vacante.asunto or vacante.titulo,
        cuerpo=texto,
        imagen_url=vacante.post_imagen_url,
        enlace_para_postular=enlace,
        visibilidad=vacante.visibilidad,
        destinatarios_internos=vacante.destinatarios_internos or [],
        programado_para=vacante.post_programado_para,
        caracteres=len(texto),
        tarjeta_titulo=vacante.asunto or vacante.titulo,
        tarjeta_descripcion=vacante.post_cuerpo or vacante.descripcion,
        tarjeta_dominio=urlparse(enlace).netloc or "",
        autor=autor,
    )


def _nombre_de_quien_publica(db: Session, usuario: Usuario) -> str:
    """Con qué nombre saldría el post: el de la cuenta conectada, si la hay."""
    token = db.get(TokenLinkedIn, usuario.id)
    if token and token.nombre_en_linkedin and not token.revocado:
        return token.nombre_en_linkedin
    return f"{usuario.nombres} {usuario.apellidos}".strip()


@router.get("/{vacante_id}/vista-previa", response_model=VistaPreviaDelPost)
def vista_previa_del_post(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VistaPreviaDelPost:
    """Cómo se verá el post. Es el mismo texto que se publica, no una aproximación."""
    vacante = _vacante_o_404(db, vacante_id)
    return _armar_vista_previa(vacante, _url_publica(request, vacante), _nombre_de_quien_publica(db, usuario))


@router.post("/vista-previa", response_model=VistaPreviaDelPost)
def vista_previa_sin_guardar(
    payload: VacanteCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> VistaPreviaDelPost:
    """La misma vista previa, pero con lo que hay escrito en el formulario.

    Existe para poder ir viendo el post **mientras se arma**, sin obligar a guardar
    una vacante a medias solo para mirarla. La vacante que se construye aquí no se
    añade a la sesión: se usa y se tira.
    """
    cargo = db.get(Cargo, payload.cargo_id)
    if cargo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado")

    vacante = Vacante(
        **payload.model_dump(exclude={"campos_personalizados", "destinatarios_internos"}),
        titulo=cargo.nombre,
        # Todavía no hay slug: lo pone el servidor al guardar. El enlace de la vista
        # previa lo dice en vez de inventarse uno que no va a existir.
        slug="(se-genera-al-guardar)",
        campos_personalizados=[c.model_dump() for c in payload.campos_personalizados],
        destinatarios_internos=[str(c) for c in payload.destinatarios_internos],
    )
    vacante.cargo = cargo
    vacante.tipo_contrato = db.get(TipoContrato, payload.tipo_contrato_id) if payload.tipo_contrato_id else None

    enlace = f"{_origen_del_frontend(request)}/postular/{vacante.slug}"
    return _armar_vista_previa(vacante, enlace, _nombre_de_quien_publica(db, usuario))


@router.post("/{vacante_id}/compartir-linkedin", response_model=ParaCompartirEnLinkedIn)
def preparar_para_compartir(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ParaCompartirEnLinkedIn:
    """Prepara el contenido y el enlace para publicar a mano en LinkedIn.

    Es la vía sin OAuth: el sistema arma el texto y abre el compositor de LinkedIn con
    la tarjeta de la vacante; quien publica es la persona, desde su propia cuenta.

    Por qué existiendo la vía con API: no necesita app aprobada, ni credenciales, ni
    tokens que caducan a los 60 días, y sirve con cualquier cuenta. A cambio, el
    sistema **no puede saber si se llegó a pulsar Publicar**, y por eso el estado que
    deja es `compartido` y no `publicado`.
    """
    vacante = _vacante_o_404(db, vacante_id)
    if vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una vacante interna no se comparte en LinkedIn. Cámbiala a pública o mixta.",
        )
    if vacante.estado != "abierta":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se comparte una vacante abierta: LinkedIn no podría mostrar un borrador.",
        )

    origen = _origen_del_frontend(request)
    # La URL que se le da a LinkedIn es la de compartir, no la del formulario: es la
    # que sirve las etiquetas Open Graph desde el servidor. Dándole la del formulario,
    # el rastreador recibiría la SPA vacía y la tarjeta saldría sin nada.
    enlace_para_linkedin = f"{origen}/compartir/{vacante.slug}"
    texto = _texto_del_post(vacante, f"{origen}/postular/{vacante.slug}")

    vacante.post_estado = "compartido"
    vacante.post_publicado_en = datetime.now(timezone.utc)
    vacante.post_error = None
    db.commit()

    return ParaCompartirEnLinkedIn(
        texto=texto,
        enlace_de_la_vacante=enlace_para_linkedin,
        url_del_compositor=(
            f"https://www.linkedin.com/sharing/share-offsite/?url={quote(enlace_para_linkedin, safe='')}"
        ),
        aviso=(
            "LinkedIn arma la tarjeta a partir del enlace y no admite texto preparado, "
            "así que el texto se copió a tu portapapeles: pégalo en el compositor antes "
            "de publicar."
        ),
    )


def _miniatura_para_linkedin(vacante: Vacante, access_token: str, persona_urn: str) -> tuple[str | None, str | None]:
    """Sube la imagen del post a LinkedIn y devuelve (urn, aviso).

    Ninguno de los problemas posibles aquí tumba la publicación: una vacante sin
    tarjeta se ve peor, pero no publicarla por la foto sería peor todavía. Lo que no
    se hace, se dice en el aviso que vuelve a la pantalla.
    """
    if not vacante.post_imagen_url:
        return None, None

    extension = Path(vacante.post_imagen_url).suffix.lower()
    if extension not in linkedin_service.FORMATOS_DE_IMAGEN_EN_LINKEDIN:
        return None, f"La imagen no se envió: LinkedIn no acepta {extension or 'ese formato'}, solo JPG, PNG o GIF."

    # La imagen vive en nuestro volumen; LinkedIn necesita los bytes, no la URL.
    relativa = vacante.post_imagen_url.split("/media/", 1)[-1]
    try:
        ruta = almacenamiento_service.ruta_de_media(relativa)
        contenido = ruta.read_bytes()
    except (HTTPException, OSError):
        return None, "La imagen no se envió: no se encontró el archivo en el servidor."

    try:
        urn = linkedin_service.subir_imagen(
            access_token=access_token,
            persona_urn=persona_urn,
            contenido=contenido,
            nombre=ruta.name,
        )
    except httpx.HTTPError as error:
        return None, f"La imagen no se envió: LinkedIn la rechazó ({error})."

    return urn, None


@router.post("/{vacante_id}/publicar-linkedin", response_model=ResultadoDePublicacion)
def publicar_en_linkedin(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    vacante = _vacante_o_404(db, vacante_id)
    if vacante.visibilidad == "interna":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una vacante interna no se publica en LinkedIn. Cámbiala a pública o mixta.",
        )

    enlace = _url_publica(request, vacante)
    texto = _texto_del_post(vacante, enlace)

    # Quien manda es el token, no las credenciales de la aplicación: uno pegado a mano
    # desde el portal de LinkedIn publica de verdad aunque no haya Client Secret ni
    # Redirect URI guardados. Mirar primero `esta_configurado` simulaba la publicación
    # teniendo con qué hacerla.
    token = db.get(TokenLinkedIn, current_user.id)
    token_usable = token is not None and not token.revocado and token.expira_en > datetime.now(timezone.utc)

    if not token_usable:
        # Sin nada con qué publicar y sin nada que conectar, modo simulado: recorre el
        # flujo entero y lo deja marcado como tal, para no hacer creer que algo salió a
        # internet. Pero si hay un token caducado o credenciales puestas, la respuesta
        # honesta es decir que hay que volver a conectar.
        if token is not None or linkedin_service.esta_configurado(db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conecta tu cuenta de LinkedIn en Configuración (o vuelve a conectarla: el acceso caducó)",
            )
        vacante.linkedin_post_id = linkedin_service._publicar_simulado(vacante.id, vacante.titulo)
        vacante.post_estado = "publicado"
        vacante.post_publicado_en = datetime.now(timezone.utc)
        vacante.post_error = None
        db.commit()
        return ResultadoDePublicacion(
            post_estado="publicado",
            linkedin_post_id=vacante.linkedin_post_id,
            simulado=True,
            mensaje="LinkedIn no está configurado: se simuló la publicación. No salió nada a internet.",
        )

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    imagen_urn, aviso_de_imagen = _miniatura_para_linkedin(vacante, access_token, token.persona_urn)

    try:
        post_id = linkedin_service.publicar_en_el_muro(
            access_token=access_token,
            persona_urn=token.persona_urn,
            texto=texto,
            enlace=enlace,
            titulo=vacante.asunto or vacante.titulo,
            descripcion=vacante.post_cuerpo or vacante.descripcion,
            imagen_urn=imagen_urn,
        )
    except httpx.HTTPError as error:
        vacante.post_estado = "error"
        vacante.post_error = str(error)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó la publicación: {error}")

    vacante.linkedin_post_id = post_id
    vacante.post_estado = "publicado"
    vacante.post_publicado_en = datetime.now(timezone.utc)
    vacante.post_error = None
    db.commit()
    return ResultadoDePublicacion(
        post_estado="publicado",
        linkedin_post_id=post_id,
        simulado=False,
        mensaje="Publicado en LinkedIn." + (f" {aviso_de_imagen}" if aviso_de_imagen else ""),
    )


def _token_usable_o_400(db: Session, usuario: Usuario) -> TokenLinkedIn:
    """El token de quien pide, o un 400 que dice qué hacer."""
    token = db.get(TokenLinkedIn, usuario.id)
    if token is None or token.revocado or token.expira_en <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conecta tu cuenta de LinkedIn en Configuración (o vuelve a conectarla: el acceso caducó)",
        )
    return token


def _post_en_linkedin_o_400(vacante: Vacante) -> str:
    """El URN del post, descartando el de las publicaciones simuladas.

    Un id simulado no existe en LinkedIn: mandarlo daría un error feo en vez de
    explicar que esa vacante nunca salió a internet.
    """
    if not vacante.linkedin_post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Esta vacante no está publicada en LinkedIn."
        )
    if "simulado" in vacante.linkedin_post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esa publicación fue simulada: no existe en LinkedIn, así que no hay nada que cambiar allí.",
        )
    return vacante.linkedin_post_id


@router.patch("/{vacante_id}/linkedin-post", response_model=ResultadoDePublicacion)
def actualizar_post_en_linkedin(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    """Reescribe el texto del post con los datos que tiene hoy la vacante.

    Es lo único que LinkedIn deja cambiar de un post publicado: ni el enlace ni la
    imagen. Sirve para una errata o para que el post deje de contradecir a la vacante
    después de editarla.
    """
    vacante = _vacante_o_404(db, vacante_id)
    post_urn = _post_en_linkedin_o_400(vacante)
    token = _token_usable_o_400(db, current_user)

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    texto = _texto_del_post(vacante, _url_publica(request, vacante))
    try:
        linkedin_service.actualizar_texto(access_token=access_token, post_urn=post_urn, texto=texto)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó el cambio: {error}")

    return ResultadoDePublicacion(
        post_estado=vacante.post_estado,
        linkedin_post_id=post_urn,
        simulado=False,
        mensaje="El texto del post se actualizó en LinkedIn. El enlace y la imagen no se pueden cambiar.",
    )


@router.delete("/{vacante_id}/linkedin-post", response_model=ResultadoDePublicacion)
def borrar_post_en_linkedin(
    vacante_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> ResultadoDePublicacion:
    """Borra el post de LinkedIn y devuelve la vacante a borrador.

    El estado vuelve a `borrador` y se olvida el id: dejarlo como publicado sería
    decir que hay algo en LinkedIn cuando ya no lo hay.
    """
    vacante = _vacante_o_404(db, vacante_id)
    post_urn = _post_en_linkedin_o_400(vacante)
    token = _token_usable_o_400(db, current_user)

    access_token = configuracion_service.cifrador().decrypt(token.access_token_cifrado.encode()).decode()
    try:
        linkedin_service.borrar_post(access_token=access_token, post_urn=post_urn)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"LinkedIn rechazó el borrado: {error}")

    vacante.linkedin_post_id = None
    vacante.post_estado = "borrador"
    vacante.post_publicado_en = None
    db.commit()
    return ResultadoDePublicacion(
        post_estado="borrador",
        linkedin_post_id=None,
        simulado=False,
        mensaje="El post se borró de LinkedIn y la vacante volvió a borrador.",
    )


@router.post("/{vacante_id}/enviar-interno", response_model=EnvioInternoOut)
def enviar_internamente(
    vacante_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("super_admin", "reclutador")),
) -> EnvioInternoOut:
    vacante = _vacante_o_404(db, vacante_id)
    if vacante.visibilidad == "publica":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta vacante es pública: no tiene envío interno. Cámbiala a interna o mixta.",
        )
    destinatarios = vacante.destinatarios_internos or []
    if not destinatarios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay destinatarios internos")

    dominios = configuracion_service.dominios_corporativos(db)
    if dominios:
        ajenos = [c for c in destinatarios if c.split("@")[-1].lower() not in dominios]
        if ajenos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estos correos no son de un dominio corporativo ({', '.join(dominios)}): "
                f"{', '.join(ajenos)}",
            )

    if not correo_service.esta_configurado(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta configurar el correo de Gmail en Configuración para poder enviar",
        )

    enlace = _url_publica(request, vacante)
    texto = _texto_del_post(vacante, enlace)
    html = "<p>" + texto.replace("\n", "<br>") + "</p>"
    try:
        enviados = correo_service.enviar(
            db,
            destinatarios=destinatarios,
            asunto=vacante.asunto or vacante.titulo,
            cuerpo_html=html,
            cuerpo_texto=texto,
        )
    except OSError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"No se pudo enviar: {error}")

    vacante.enviado_internamente_en = datetime.now(timezone.utc)
    db.commit()
    return EnvioInternoOut(enviados=enviados, mensaje=f"Enviado a {enviados} destinatario(s).")


@router.get("/{vacante_id}/share-whatsapp", response_model=WhatsAppShareOut)
def compartir_whatsapp(
    vacante_id: UUID, request: Request, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> WhatsAppShareOut:
    vacante = _vacante_o_404(db, vacante_id)
    return WhatsAppShareOut(
        whatsapp_url=whatsapp_service.build_share_link(vacante.titulo, _url_publica(request, vacante))
    )
