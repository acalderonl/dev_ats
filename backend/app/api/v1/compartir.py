"""Página de la vacante pensada para los rastreadores de redes sociales.

El problema que resuelve, comprobado pidiendo la página con el agente de LinkedIn: la
aplicación es una SPA, así que lo que llega al rastreador es `<div id="root"></div>` y
el título genérico del sitio. Sin JavaScript no hay nada que leer, y LinkedIn armaría
una tarjeta vacía: sin puesto, sin descripción y sin imagen.

Esta página sí se genera en el servidor, con las etiquetas Open Graph rellenas. Es la
URL que se comparte; **una persona que la abra se va al formulario de verdad** por la
redirección, así que no es una página paralela que haya que mantener.

No se usa SSR del frontend a propósito: montar renderizado en servidor para cuatro
etiquetas sería cambiar la arquitectura entera por un caso que se resuelve con esto.
"""

import json
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.limites import limitar
from app.models.vacante import Vacante

router = APIRouter()

# Lo que LinkedIn muestra bajo el título. Más largo que esto lo corta él.
LARGO_DE_LA_DESCRIPCION = 200


def _origen(request: Request) -> str:
    return (request.headers.get("origin") or get_settings().frontend_origin).rstrip("/")


def _resumen(vacante: Vacante) -> str:
    """Una línea con lo que decide a alguien a pulsar: qué, cuánto y en qué horario."""
    partes = []
    if vacante.tipo_contrato:
        partes.append(vacante.tipo_contrato.nombre)
    if vacante.remuneracion is not None:
        partes.append(f"${vacante.remuneracion:,.2f}")
    if vacante.hora_entrada and vacante.hora_salida:
        partes.append(f"{vacante.hora_entrada:%H:%M}–{vacante.hora_salida:%H:%M}")

    cabecera = " · ".join(partes)
    cuerpo = " ".join((vacante.post_cuerpo or vacante.descripcion or "").split())
    texto = f"{cabecera}. {cuerpo}" if cabecera else cuerpo
    if len(texto) > LARGO_DE_LA_DESCRIPCION:
        texto = texto[: LARGO_DE_LA_DESCRIPCION - 1].rsplit(" ", 1)[0] + "…"
    return texto or "Vacante abierta en la Academia Naval Almirante Illingworth."


@router.get("/{slug}", response_class=HTMLResponse, dependencies=[Depends(limitar("consulta"))])
def pagina_para_compartir(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Devuelve la vacante con sus etiquetas Open Graph, y redirige a quien sea humano."""
    vacante = db.scalar(select(Vacante).options(selectinload(Vacante.tipo_contrato)).where(Vacante.slug == slug))
    if vacante is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")

    # Las mismas reglas que el portal: un borrador o una vacante interna no se comparte,
    # por mucho que alguien tenga el enlace.
    limite = vacante.fecha_limite
    if limite.tzinfo is None:
        limite = limite.replace(tzinfo=timezone.utc)
    if vacante.estado != "abierta" or vacante.visibilidad == "interna" or limite < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esta vacante no está disponible")

    origen = _origen(request)
    destino = f"{origen}/postular/{vacante.slug}"
    titulo = f"{vacante.asunto or vacante.titulo} — ANAI"
    descripcion = _resumen(vacante)
    # Solo se anuncia imagen si la vacante tiene una de verdad. El escudo no sirve de
    # respaldo: es un SVG, y LinkedIn no los dibuja en las tarjetas —saldría un hueco
    # en vez de una imagen—. Sin `og:image`, muestra una tarjeta solo de texto, que se
    # ve bien. La subida ya obliga a JPG, PNG, GIF o WebP.
    imagen = vacante.post_imagen_url
    if imagen and imagen.startswith("/"):
        imagen = f"{origen}{imagen}"

    etiquetas_de_imagen = (
        f'<meta property="og:image" content="{escape(imagen)}">\n'
        f'<meta name="twitter:image" content="{escape(imagen)}">'
        if imagen
        else "<!-- Sin imagen: la vacante no tiene una subida. -->"
    )

    # `escape` en todo lo que viene de la base: el título y la descripción los escribe
    # una persona, y sin esto unas comillas romperían el atributo o algo peor.
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descripcion)}">
<link rel="canonical" href="{escape(destino)}">

<meta property="og:type" content="website">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descripcion)}">
<meta property="og:url" content="{escape(destino)}">
{etiquetas_de_imagen}
<meta property="og:site_name" content="Academia Naval Almirante Illingworth">
<meta property="og:locale" content="es_EC">

<meta name="twitter:card" content="{'summary_large_image' if imagen else 'summary'}">
<meta name="twitter:title" content="{escape(titulo)}">
<meta name="twitter:description" content="{escape(descripcion)}">

<!-- El rastreador se queda con las etiquetas de arriba; una persona sigue de largo. -->
<meta http-equiv="refresh" content="0; url={escape(destino)}">
</head>
<body>
<p>Llevándote a la vacante… <a href="{escape(destino)}">{escape(titulo)}</a></p>
<script>location.replace({json.dumps(destino)});</script>
</body>
</html>"""

    return HTMLResponse(
        content=html,
        # Que LinkedIn no se quede con una versión vieja de la tarjeta si se edita la
        # vacante, pero tampoco vuelva a pedirla en cada visita.
        headers={"Cache-Control": "public, max-age=300"},
    )
