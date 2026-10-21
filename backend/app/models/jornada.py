"""Jornadas laborales configurables.

El formulario de la vacante pide primero la jornada, luego la hora de entrada, y
calcula la de salida. Las opciones no están en el código: se administran desde la
pantalla de Configuración, porque cuántas horas trabaja una empresa cambia por país,
por contrato y por puesto.

`horas` admite medias horas (7,5) y por eso es `Numeric`, no entero.
"""

from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Jornada(Base):
    __tablename__ = "jornadas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    horas: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
