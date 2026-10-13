"""Envío del post interno por correo, con Gmail / Google Workspace.

Gmail no acepta la contraseña normal de la cuenta desde un programa: hay que generar
una **contraseña de aplicación** (16 caracteres) en la cuenta de Google, con la
verificación en dos pasos activada. Se guarda cifrada en `configuracion`.

El envío es síncrono a propósito. Con la lista de correos corporativos de una empresa
—decenas, no miles— tarda segundos, y a cambio quien pulsa "enviar" se entera en el
acto de si falló. Si algún día la lista crece, esto es lo que hay que mover a una cola.
"""

import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.services import configuracion_service

SERVIDOR = "smtp.gmail.com"
PUERTO = 465


class CorreoNoConfigurado(RuntimeError):
    """Faltan remitente o contraseña de aplicación."""


def esta_configurado(db: Session) -> bool:
    remitente = configuracion_service.leer(db, "gmail_remitente")
    clave = configuracion_service.leer_secreto(db, "gmail_password_app")
    return bool(remitente and clave)


def enviar(db: Session, *, destinatarios: list[str], asunto: str, cuerpo_html: str, cuerpo_texto: str) -> int:
    """Envía el mismo mensaje a cada destinatario. Devuelve cuántos salieron.

    Van en copia oculta: si fueran visibles, cada persona de la empresa vería la
    lista completa de a quién más se le ofreció la vacante.
    """
    remitente = configuracion_service.leer(db, "gmail_remitente")
    clave = configuracion_service.leer_secreto(db, "gmail_password_app")
    if not (remitente and clave):
        raise CorreoNoConfigurado(
            "Falta configurar el remitente de Gmail y su contraseña de aplicación en Configuración"
        )
    if not destinatarios:
        return 0

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = remitente
    mensaje["Bcc"] = ", ".join(destinatarios)
    mensaje.set_content(cuerpo_texto)
    mensaje.add_alternative(cuerpo_html, subtype="html")

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL(SERVIDOR, PUERTO, context=contexto, timeout=30) as servidor:
        servidor.login(remitente, clave)
        servidor.send_message(mensaje)
    return len(destinatarios)
