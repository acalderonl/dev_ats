"""Motor de extracción heurística de datos desde CVs en PDF/DOCX.

No usa NLP ni modelos de IA: aplica expresiones regulares y palabras clave sobre el
texto plano extraído del documento. Es un punto de partida funcional; CVs con
formatos muy variados requerirán ajustar los patrones o incorporar un modelo de
extracción de entidades más adelante.
"""

import io
import re

import docx2txt
import pdfplumber
from fastapi import HTTPException, UploadFile, status

from app.schemas.postulante import CvParseadoOut, ExperienciaLaboral, FormacionSuperior

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?593|0)?\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b|\b0\d{9}\b")
CEDULA_RE = re.compile(r"\b\d{10}\b")
EDAD_RE = re.compile(r"\bedad[:\s]+(\d{1,2})\b", re.IGNORECASE)
RANGO_FECHAS_RE = re.compile(
    r"(\d{4})\s*[-–a]{1,3}\s*(\d{4}|actualidad|presente|actual)", re.IGNORECASE
)

NIVEL_KEYWORDS: list[tuple[str, str]] = [
    ("maestría", "Cuarto Nivel"),
    ("máster", "Cuarto Nivel"),
    ("posgrado", "Cuarto Nivel"),
    ("mba", "Cuarto Nivel"),
    ("ingenier", "Tercer Nivel"),
    ("licenciad", "Tercer Nivel"),
    ("universi", "Tercer Nivel"),
    ("tecnológ", "Tecnológico"),
    ("técnic", "Técnico"),
]

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def _extract_text_from_pdf(raw: bytes) -> str:
    text_chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def _extract_text_from_docx(raw: bytes) -> str:
    with io.BytesIO(raw) as buffer:
        return docx2txt.process(buffer) or ""


def _guess_nombres_apellidos(lines: list[str]) -> tuple[str | None, str | None]:
    for line in lines[:5]:
        cleaned = line.strip()
        words = [w for w in cleaned.split() if w.isalpha()]
        if 2 <= len(words) <= 5 and cleaned == cleaned.title():
            mid = max(1, len(words) // 2)
            return " ".join(words[:mid]), " ".join(words[mid:])
    return None, None

def _guess_nivel_instruccion(text_lower: str) -> str | None:
    for keyword, nivel in NIVEL_KEYWORDS:
        if keyword in text_lower:
            return nivel
    return None


def _guess_experiencia(lines: list[str]) -> list[ExperienciaLaboral]:
    experiencias: list[ExperienciaLaboral] = []
    for line in lines:
        match = RANGO_FECHAS_RE.search(line)
        if not match:
            continue
        desde, hasta_raw = match.group(1), match.group(2)
        actualmente = hasta_raw.lower() in {"actualidad", "presente", "actual"}
        experiencias.append(
            ExperienciaLaboral(
                cargo=line.split("-")[0].strip()[:120] if "-" in line else line.strip()[:120],
                empresa=None,
                fecha_desde=f"{desde}-01-01",
                fecha_hasta=None if actualmente else f"{hasta_raw}-01-01",
                actualmente=actualmente,
            )
        )
        if len(experiencias) >= 5:
            break
    return experiencias


def parse_cv_text(raw_text: str) -> CvParseadoOut:
    lines = [line for line in raw_text.splitlines() if line.strip()]
    text_lower = raw_text.lower()

    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)
    cedula_match = CEDULA_RE.search(raw_text)
    edad_match = EDAD_RE.search(text_lower)
    nombres, apellidos = _guess_nombres_apellidos(lines)

    return CvParseadoOut(
        nombres=nombres,
        apellidos=apellidos,
        edad=int(edad_match.group(1)) if edad_match else None,
        cedula=cedula_match.group(0) if cedula_match else None,
        email=email_match.group(0) if email_match else None,
        telefono=phone_match.group(0) if phone_match else None,
        formacion_superior=FormacionSuperior(estado="por confirmar") if "universi" in text_lower else None,
        nivel_instruccion=_guess_nivel_instruccion(text_lower),
        titulos=[],
        experiencia_laboral=_guess_experiencia(lines),
        texto_extraido_parcial=raw_text[:500],
    )


async def parse_cv_upload(file: UploadFile) -> CvParseadoOut:
    filename = (file.filename or "").lower()
    extension = next((ext for ext in SUPPORTED_EXTENSIONS if filename.endswith(ext)), None)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Sube un archivo .pdf, .docx o .doc",
        )

    raw = await file.read()

    if extension == ".pdf":
        text = _extract_text_from_pdf(raw)
    elif extension == ".docx":
        text = _extract_text_from_docx(raw)
    else:
        # El formato .doc binario legado no tiene un parser puro-Python confiable;
        # se recomienda convertir a .docx o .pdf antes de subir.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El formato .doc no puede analizarse automáticamente. Convierte el archivo a .docx o .pdf.",
        )

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo extraer texto del documento. Verifica que no sea un escaneo de imagen.",
        )

    return parse_cv_text(text)
