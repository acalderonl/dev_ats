"""Cómo se arma el post de una convocatoria.

Vive en un servicio y no en el router porque lo usan dos sitios que no se hablan: la
publicación real (desde `/convocatorias`) y la vista previa sin guardar (desde
`/vacantes`). Si cada uno armara el texto por su cuenta, la simulación enseñaría algo
*parecido* a lo que sale, y "parecido" no sirve para decidir si el post está listo.
"""

from urllib.parse import urlparse

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.utils import normalizar
from app.models.convocatoria import Convocatoria
from app.models.usuario import Usuario
from app.models.vacante import TokenLinkedIn, Vacante
from app.schemas.convocatoria import VistaPreviaDelPost


def origen_del_frontend(request: Request) -> str:
    return request.headers.get("origin") or get_settings().frontend_origin


def url_publica(request: Request, convocatoria: Convocatoria) -> str:
    """El enlace por el que entra el postulante. Es de la convocatoria, no de la vacante."""
    return f"{origen_del_frontend(request)}/postular/{convocatoria.slug}"


def etiqueta(texto: str) -> str:
    """Convierte un nombre en una etiqueta: `#AnalistaDeReclutamiento`.

    Sin tildes ni eñes a propósito: LinkedIn las admite, pero una etiqueta con tilde y
    otra sin ella son dos etiquetas distintas, y quien busca escribe la fácil.
    """
    limpio = normalizar(texto)
    return "#" + "".join(palabra.capitalize() for palabra in limpio.split() if palabra.isalnum())


def etiquetas(vacante: Vacante) -> str:
    """Las etiquetas del post, sin repetir y sin las vacías."""
    candidatas = ["#Empleo", etiqueta(vacante.titulo)]
    if vacante.cargo and vacante.cargo.clasificacion:
        candidatas.append(etiqueta(vacante.cargo.clasificacion))

    vistas: list[str] = []
    for e in candidatas:
        if len(e) > 1 and e not in vistas:
            vistas.append(e)
    return " ".join(vistas)


def texto_del_post(convocatoria: Convocatoria, enlace: str) -> str:
    """El texto que se publica. Las condiciones salen de la vacante; el ciclo, de aquí."""
    vacante = convocatoria.vacante
    partes = [convocatoria.asunto or vacante.titulo, "", convocatoria.post_cuerpo or vacante.descripcion]
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
    partes.append(f"Postulaciones hasta el {convocatoria.fecha_limite:%d/%m/%Y}")
    partes += ["", f"Postula aquí: {enlace}", "", etiquetas(vacante)]
    return "\n".join(partes)


def nombre_de_quien_publica(db: Session, usuario: Usuario) -> str:
    """Con qué nombre saldría el post: el de la cuenta conectada, si la hay."""
    token = db.get(TokenLinkedIn, usuario.id)
    if token and token.nombre_en_linkedin and not token.revocado:
        return token.nombre_en_linkedin
    return f"{usuario.nombres} {usuario.apellidos}".strip()


def armar_vista_previa(convocatoria: Convocatoria, enlace: str, autor: str) -> VistaPreviaDelPost:
    """Lo que se verá, construido con las **mismas** piezas que se publican."""
    vacante = convocatoria.vacante
    texto = texto_del_post(convocatoria, enlace)
    return VistaPreviaDelPost(
        asunto=convocatoria.asunto or vacante.titulo,
        cuerpo=texto,
        imagen_url=convocatoria.post_imagen_url,
        enlace_para_postular=enlace,
        visibilidad=vacante.visibilidad,
        destinatarios_internos=vacante.destinatarios_internos or [],
        programado_para=convocatoria.post_programado_para,
        caracteres=len(texto),
        tarjeta_titulo=convocatoria.asunto or vacante.titulo,
        tarjeta_descripcion=convocatoria.post_cuerpo or vacante.descripcion,
        tarjeta_dominio=urlparse(enlace).netloc or "",
        autor=autor,
    )
