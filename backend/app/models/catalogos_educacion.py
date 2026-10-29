"""Catálogos de la sección 4 del cargo (educación formal requerida).

Son tres tablas con la misma forma. Cada una es su propia tabla, y no una sola tabla con
una columna "tipo", para que la base garantice que `nivel_educacion_id` apunta a un nivel y
no a un área: la integridad la hace PostgreSQL, no el código.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class _CatalogoBase:
    """Forma común: identificador, nombre único y si sigue ofreciéndose."""

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NivelEducacion(_CatalogoBase, Base):
    """Bachillerato, Tercer Nivel, Maestría... (niveles de la LOES)."""

    __tablename__ = "niveles_educacion"


class TituloAcademico(_CatalogoBase, Base):
    """El título que se obtiene: Ingeniero/a, Licenciado/a, Tecnólogo/a..."""

    __tablename__ = "titulos_academicos"


class AreaAcademica(_CatalogoBase, Base):
    """Área de especialización, según la clasificación CINE de la UNESCO."""

    __tablename__ = "areas_academicas"
