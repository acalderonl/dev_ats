"""Lectura del CV con Claude para rellenar el formulario de postulación.

Por qué no con expresiones regulares: el formulario pide ~40 campos, con tres listas
anidadas donde cada entrada tiene su institución, su nivel, su estado y sus fechas de
inicio y fin. Emparejar "Junio 2019 – Junio 2024" con la carrera correcta, o deducir
que "Especialista de Talento Humano" es un puesto senior, no es un problema de
patrones. El extractor anterior lo intentaba y fallaba en todo lo que no fuera el
correo o el teléfono.

Dos decisiones que importan:

- **El PDF se manda tal cual, no como texto extraído.** Un CV es un documento con
  columnas, tablas y barras laterales; al aplanarlo con `pdfplumber` las fechas se
  despegan de su empleo y el orden de lectura se pierde. Mandando el PDF, el modelo
  ve la página. Los `.docx` sí van como texto, porque no hay otra forma.
- **Lo que no esté en el CV se queda vacío.** Está dicho en el prompt y en el esquema
  (todo opcional). Una casilla vacía la rellena el candidato en diez segundos; un dato
  inventado se queda en la ficha para siempre porque nadie lo vuelve a mirar.

Sin clave configurada no se rompe: cae a las heurísticas de siempre y **lo declara**
en `motor`, para que la pantalla no haga creer que leyó algo que no leyó.
"""

import base64

import anthropic
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.schemas.cv_extraido import CvExtraido, CvExtraidoOut
from app.services import configuracion_service

MODELO_POR_DEFECTO = "claude-opus-5-5"

# Un CV largo son unas 10 páginas. El techo de salida va holgado porque la
# experiencia detallada de alguien con 20 años de carrera ocupa.
MAXIMO_TOKENS = 16000
TIEMPO_LIMITE = 120.0

INSTRUCCIONES = """Eres un asistente de recursos humanos que lee currículums y extrae sus datos \
para rellenar un formulario de postulación.

Reglas, en orden de importancia:

1. **No inventes nada.** Si un dato no está en el documento, déjalo vacío (null). Es \
preferible una casilla vacía a un dato supuesto: el candidato la completa, pero un \
dato inventado se queda en su ficha sin que nadie lo revise.
2. **No deduzcas datos sensibles.** El género y la nacionalidad solo se rellenan si el \
documento los dice literalmente. No los infieras del nombre, de la foto ni del país.
3. Copia los textos **como aparecen**, sin corregir mayúsculas ni traducir. Los \
títulos y nombres de empresa se respetan tal cual.
4. Las fechas van por mes y año separados. Si el CV solo da el año, deja el mes vacío. \
"Actualidad", "presente" o "a la fecha" significan `actualmente: true` y fin vacío.
5. Ordena educación y experiencia **de más reciente a más antigua**.
6. `jerarquia` solo si se deduce con claridad del puesto o de las funciones. Ante la \
duda, vacío.
7. En `descripcion` resume las funciones reales que liste el CV. No las adornes ni \
añadas logros que no estén escritos.
"""


class ExtraccionNoConfigurada(RuntimeError):
    """Falta la clave de la API."""


def modelo_elegido(db: Session) -> str:
    return configuracion_service.leer(db, "anthropic_modelo") or MODELO_POR_DEFECTO


def esta_configurado(db: Session) -> bool:
    return configuracion_service.leer_secreto(db, "anthropic_api_key") is not None


def _cliente(db: Session) -> anthropic.Anthropic:
    clave = configuracion_service.leer_secreto(db, "anthropic_api_key")
    if not clave:
        raise ExtraccionNoConfigurada("Falta la clave de la API de Claude en Configuración para poder leer el CV")
    return anthropic.Anthropic(api_key=clave, timeout=TIEMPO_LIMITE)


def _contenido_del_mensaje(contenido: bytes, es_pdf: bool, texto: str | None) -> list[dict]:
    """El PDF viaja como documento; el resto, como texto ya extraído."""
    if es_pdf:
        return [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.b64encode(contenido).decode(),
                },
            },
            {"type": "text", "text": "Extrae los datos de este currículum."},
        ]
    return [{"type": "text", "text": f"Extrae los datos de este currículum:\n\n{texto or ''}"}]


def _cuantos_campos_trae(extraido: CvExtraido) -> int:
    """Cuántos datos se encontraron de verdad. Es lo que distingue 'leyó poco' de 'falló'."""
    sueltos = sum(
        1
        for campo, valor in extraido.model_dump().items()
        if campo not in ("educacion", "idiomas", "experiencia", "otras_redes") and valor not in (None, "")
    )
    return sueltos + len(extraido.educacion) + len(extraido.idiomas) + len(extraido.experiencia)


def extraer(db: Session, *, contenido: bytes, es_pdf: bool, texto: str | None = None) -> CvExtraidoOut:
    """Lee el CV y devuelve los campos del formulario.

    Lanza `ExtraccionNoConfigurada` si falta la clave; quien llama decide si cae a las
    heurísticas o avisa.
    """
    cliente = _cliente(db)

    respuesta = cliente.messages.parse(
        model=modelo_elegido(db),
        max_tokens=MAXIMO_TOKENS,
        system=INSTRUCCIONES,
        messages=[{"role": "user", "content": _contenido_del_mensaje(contenido, es_pdf, texto)}],
        output_format=CvExtraido,
    )

    extraido = respuesta.parsed_output
    if extraido is None:
        # El modelo puede quedarse sin tokens o declinar; se trata como lectura vacía
        # en vez de reventar la postulación.
        return CvExtraidoOut(
            motor="claude",
            aviso="No se pudo leer el documento. Rellena el formulario a mano.",
            campos_encontrados=0,
        )

    encontrados = _cuantos_campos_trae(extraido)
    return CvExtraidoOut(
        **extraido.model_dump(),
        motor="claude",
        campos_encontrados=encontrados,
        aviso=("Se leyeron pocos datos del documento: revisa el formulario con calma." if encontrados < 5 else None),
    )


# --------------------------------------------------------------- Punto de entrada


def _desde_heuristicas(texto: str) -> CvExtraidoOut:
    """Lo que se puede sacar sin salir a internet: correo, teléfono, cédula y poco más.

    Es la red de seguridad, no el camino principal. Se marca `motor='heuristicas'`
    para que la pantalla pueda decir que el llenado fue parcial.
    """
    from app.services.cv_parser_service import parse_cv_text

    basico = parse_cv_text(texto)
    extraido = CvExtraido(
        nombres=basico.nombres,
        apellidos=basico.apellidos,
        email=basico.email,
        numero_documento=basico.cedula,
        telefono=basico.telefono,
    )
    return CvExtraidoOut(
        **extraido.model_dump(),
        motor="heuristicas",
        campos_encontrados=_cuantos_campos_trae(extraido),
        aviso=(
            "La lectura automática del CV no está configurada, así que solo se "
            "rellenaron los datos básicos. Completa el resto a mano."
        ),
    )


async def leer_cv(db: Session, archivo: UploadFile) -> CvExtraidoOut:
    """Lee el CV subido y devuelve los campos del formulario.

    El orden importa: se intenta Claude y **solo** se cae a las heurísticas si no hay
    clave configurada. Un fallo de red o de la API no se disimula: se devuelve el
    aviso, porque si la clave está puesta el usuario espera la lectura buena y
    rellenarle cuatro campos en silencio le haría creer que el CV se leyó entero.
    """
    from app.services.cv_parser_service import extraer_texto_de_cv

    contenido, texto, es_pdf = await extraer_texto_de_cv(archivo)

    if not esta_configurado(db):
        return _desde_heuristicas(texto)

    try:
        return extraer(db, contenido=contenido, es_pdf=es_pdf, texto=texto)
    except anthropic.APIStatusError as error:
        salida = _desde_heuristicas(texto)
        salida.aviso = (
            f"La lectura automática falló ({error.status_code}) y solo se rellenaron los "
            "datos básicos. Revisa el formulario completo."
        )
        return salida
    except (anthropic.APIConnectionError, anthropic.APITimeoutError):
        salida = _desde_heuristicas(texto)
        salida.aviso = (
            "No se pudo contactar con el servicio de lectura; solo se rellenaron los "
            "datos básicos. Revisa el formulario completo."
        )
        return salida
