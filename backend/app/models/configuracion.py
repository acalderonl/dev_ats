"""Parámetros que se editan desde la aplicación, no desde el código.

Aquí viven las credenciales de LinkedIn y de Gmail. Guardarlas en la base y no en
variables de entorno es lo que pidió el dueño —se administran desde la pantalla de
Configuración— y tiene una consecuencia que esta tabla asume: **los valores marcados
como secretos se guardan cifrados**, nunca en claro.

El cifrado es Fernet con una clave derivada de `SECRET_KEY` (ver `config.py`). La API
jamás devuelve un valor secreto: devuelve si está puesto y sus últimos caracteres, que
es lo justo para que una persona reconozca cuál configuró.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Configuracion(Base):
    __tablename__ = "configuracion"

    clave: Mapped[str] = mapped_column(String(100), primary_key=True)
    # Cifrado si `es_secreto`; en claro si no. El tipo es el mismo: lo que cambia es
    # quién puede leerlo, no cómo se almacena.
    valor: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_secreto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
