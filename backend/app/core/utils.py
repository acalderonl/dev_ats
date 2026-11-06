import re
import unicodedata
import uuid


def normalizar(texto: str) -> str:
    """Versión comparable de un texto: sin tildes, en minúsculas y sin espacios de más.

    Es lo que permite detectar que "Programación Orientada a Objetos" y
    "programacion orientada a objetos" son lo mismo.
    """
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sin_tildes.lower().split())


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{suffix}"
