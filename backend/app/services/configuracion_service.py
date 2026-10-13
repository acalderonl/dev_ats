"""Lectura y escritura de los parámetros que se editan desde la aplicación.

Los valores marcados como secretos se guardan **cifrados** (Fernet, con una clave
derivada de `SECRET_KEY`) y la API nunca los devuelve. Para que una persona reconozca
cuál configuró sin exponerlo, se devuelve una pista: los últimos cuatro caracteres.

Qué pasa si se rota `SECRET_KEY`: los secretos guardados dejan de poder descifrarse.
`leer_secreto` devuelve `None` en ese caso en vez de reventar, y la pantalla de
Configuración lo muestra como "no configurado" para que se vuelvan a introducir.
"""

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.configuracion import Configuracion

# Clave -> es_secreto. Declarar las claves evita que un error de escritura cree una
# entrada nueva en silencio y deje la verdadera sin tocar.
CLAVES = {
    "empresa_nombre": False,
    "linkedin_client_id": False,
    "linkedin_client_secret": True,
    "linkedin_redirect_uri": False,
    "gmail_remitente": False,
    "gmail_password_app": True,
    "dominios_corporativos": False,
}

LARGO_DE_LA_PISTA = 4


def _cifrador() -> Fernet:
    return Fernet(get_settings().clave_de_cifrado())


def es_clave_valida(clave: str) -> bool:
    return clave in CLAVES


def escribir(db: Session, clave: str, valor: str | None) -> None:
    """Guarda un parámetro. Si es secreto, lo cifra antes."""
    if clave not in CLAVES:
        raise ValueError(f"Parámetro desconocido: {clave}")

    es_secreto = CLAVES[clave]
    limpio = (valor or "").strip()
    almacenado: str | None
    if not limpio:
        almacenado = None
    elif es_secreto:
        almacenado = _cifrador().encrypt(limpio.encode()).decode()
    else:
        almacenado = limpio

    fila = db.get(Configuracion, clave)
    if fila is None:
        db.add(Configuracion(clave=clave, valor=almacenado, es_secreto=es_secreto))
    else:
        fila.valor = almacenado
        fila.es_secreto = es_secreto


def leer(db: Session, clave: str) -> str | None:
    """Devuelve un parámetro NO secreto."""
    fila = db.get(Configuracion, clave)
    return fila.valor if fila else None


def leer_secreto(db: Session, clave: str) -> str | None:
    """Descifra un parámetro secreto.

    Devuelve `None` si no está puesto o si no se puede descifrar (por ejemplo, porque
    se rotó `SECRET_KEY`). Quien llama debe tratar ambos casos igual: falta configurar.
    """
    fila = db.get(Configuracion, clave)
    if fila is None or not fila.valor:
        return None
    try:
        return _cifrador().decrypt(fila.valor.encode()).decode()
    except InvalidToken:
        return None


def pista(db: Session, clave: str) -> str | None:
    """Últimos caracteres de un secreto, para reconocerlo sin verlo entero."""
    valor = leer_secreto(db, clave)
    if not valor:
        return None
    return f"...{valor[-LARGO_DE_LA_PISTA:]}" if len(valor) > LARGO_DE_LA_PISTA else "..."


def estado_de_configuracion(db: Session) -> dict:
    """Lo que ve la pantalla de Configuración: valores en claro y pistas de los secretos."""
    salida: dict[str, object] = {}
    for clave, es_secreto in CLAVES.items():
        if es_secreto:
            salida[clave] = None
            salida[f"{clave}_configurado"] = leer_secreto(db, clave) is not None
            salida[f"{clave}_pista"] = pista(db, clave)
        else:
            salida[clave] = leer(db, clave)
    return salida


def dominios_corporativos(db: Session) -> list[str]:
    """Dominios que cuentan como 'interno'. Sin configurar, no se restringe nada."""
    crudo = leer(db, "dominios_corporativos") or ""
    return [d.strip().lower().lstrip("@") for d in crudo.split(",") if d.strip()]
