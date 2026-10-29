"""Envío del post interno por correo.

Dos formas de conectarse, que se eligen en Configuración:

- **Gmail / Google Workspace**: servidor y puerto fijos, porque son siempre los mismos.
  Gmail no acepta la contraseña normal de la cuenta desde un programa: hay que generar
  una **contraseña de aplicación** de 16 caracteres, con la verificación en dos pasos
  activada.
- **Servidor propio (SMTP)**: para el correo institucional de la empresa. Aquí se
  pregunta todo —servidor, puerto, cifrado, usuario y contraseña— porque cada
  institución tiene el suyo.

Gmail es, por dentro, el caso particular del segundo con los valores ya puestos. Se
mantienen separados en la pantalla porque lo que hay que pedirle a una persona es muy
distinto: para Gmail, una contraseña de aplicación; para un servidor propio, cinco
datos que tiene que darle su departamento de sistemas.

El envío es síncrono a propósito. Con la lista de correos de una empresa —decenas, no
miles— tarda segundos, y a cambio quien pulsa "enviar" se entera en el acto de si
falló. Si algún día la lista crece, esto es lo que hay que mover a una cola.
"""

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.services import configuracion_service

TIPOS = ("gmail", "smtp")
CIFRADOS = ("ssl", "starttls", "ninguna")

GMAIL_SERVIDOR = "smtp.gmail.com"
GMAIL_PUERTO = 465

TIEMPO_LIMITE = 30


class CorreoNoConfigurado(RuntimeError):
    """Falta algún dato para poder conectarse."""


@dataclass(frozen=True)
class Conexion:
    """Los datos ya resueltos, vengan de Gmail o de un servidor propio."""

    servidor: str
    puerto: int
    cifrado: str
    usuario: str
    clave: str
    remitente: str


def tipo_elegido(db: Session) -> str:
    """Qué conexión está seleccionada. Sin elegir, Gmail: es lo que había antes."""
    return configuracion_service.leer(db, "correo_tipo") or "gmail"


def _conexion_gmail(db: Session) -> Conexion | None:
    remitente = configuracion_service.leer(db, "gmail_remitente")
    clave = configuracion_service.leer_secreto(db, "gmail_password_app")
    if not (remitente and clave):
        return None
    return Conexion(
        servidor=GMAIL_SERVIDOR,
        puerto=GMAIL_PUERTO,
        cifrado="ssl",
        usuario=remitente,
        clave=clave,
        remitente=remitente,
    )


def _conexion_smtp(db: Session) -> Conexion | None:
    servidor = configuracion_service.leer(db, "smtp_servidor")
    puerto = configuracion_service.leer(db, "smtp_puerto")
    remitente = configuracion_service.leer(db, "smtp_remitente")
    clave = configuracion_service.leer_secreto(db, "smtp_password")
    if not (servidor and puerto and remitente and clave):
        return None
    # El usuario de autenticación no siempre es el remitente: hay servidores donde se
    # entra con `dominio\usuario` o con una cuenta de servicio.
    usuario = configuracion_service.leer(db, "smtp_usuario") or remitente
    cifrado = configuracion_service.leer(db, "smtp_cifrado") or "starttls"
    return Conexion(
        servidor=servidor,
        puerto=int(puerto),
        cifrado=cifrado,
        usuario=usuario,
        clave=clave,
        remitente=remitente,
    )


def conexion(db: Session) -> Conexion | None:
    """La conexión del tipo elegido, o None si le falta algún dato."""
    return _conexion_gmail(db) if tipo_elegido(db) == "gmail" else _conexion_smtp(db)


def esta_configurado(db: Session) -> bool:
    return conexion(db) is not None


def _que_falta(db: Session) -> str:
    if tipo_elegido(db) == "gmail":
        return "Falta el correo remitente de Gmail o su contraseña de aplicación (Configuración)"
    return "Faltan datos del servidor SMTP: servidor, puerto, remitente o contraseña (Configuración)"


def _abrir(datos: Conexion):
    """Abre la sesión SMTP según el cifrado elegido.

    `ninguna` existe porque algunos servidores internos no ofrecen cifrado, pero manda
    la contraseña en claro por la red: la pantalla lo advierte.
    """
    if datos.cifrado == "ssl":
        return smtplib.SMTP_SSL(
            datos.servidor, datos.puerto, context=ssl.create_default_context(), timeout=TIEMPO_LIMITE
        )
    sesion = smtplib.SMTP(datos.servidor, datos.puerto, timeout=TIEMPO_LIMITE)
    if datos.cifrado == "starttls":
        sesion.starttls(context=ssl.create_default_context())
    return sesion


def probar(db: Session) -> str:
    """Se conecta y autentica sin mandar nada. Devuelve un texto para la pantalla.

    Existe para no tener que descubrir que la configuración estaba mal **enviando una
    vacante real a una lista de correos de verdad**.
    """
    datos = conexion(db)
    if datos is None:
        raise CorreoNoConfigurado(_que_falta(db))

    with _abrir(datos) as sesion:
        sesion.login(datos.usuario, datos.clave)
    return f"Conexión correcta con {datos.servidor}:{datos.puerto} como {datos.remitente}."


def enviar(db: Session, *, destinatarios: list[str], asunto: str, cuerpo_html: str, cuerpo_texto: str) -> int:
    """Envía el mismo mensaje a cada destinatario. Devuelve cuántos salieron.

    Van en copia oculta: si fueran visibles, cada persona de la empresa vería la lista
    completa de a quién más se le ofreció la vacante.
    """
    datos = conexion(db)
    if datos is None:
        raise CorreoNoConfigurado(_que_falta(db))
    if not destinatarios:
        return 0

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = datos.remitente
    mensaje["To"] = datos.remitente
    mensaje["Bcc"] = ", ".join(destinatarios)
    mensaje.set_content(cuerpo_texto)
    mensaje.add_alternative(cuerpo_html, subtype="html")

    with _abrir(datos) as sesion:
        sesion.login(datos.usuario, datos.clave)
        sesion.send_message(mensaje)
    return len(destinatarios)
