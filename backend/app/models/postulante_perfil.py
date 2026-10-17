"""Las tres listas del perfil del postulante: educación, idiomas y experiencia.

Antes vivían como JSONB dentro de `postulantes` (`formacion_superior`,
`experiencia_laboral`). Pasan a tablas porque dejaron de ser un apunte y son datos
que hay que **filtrar y buscar**: "quién habla inglés avanzado", "quién estudió en tal
universidad", "quién tiene experiencia en educación". Eso sobre JSONB se puede hacer,
pero se escribe peor y no se indexa igual.

Las fechas se guardan como **mes y año por separado**, no como fecha completa. Un CV
dice "Junio 2019", no "15 de junio de 2019": inventar el día sería precisión falsa.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class _FilaDePerfil(Base):
    """Lo común a las tres: a quién pertenece y en qué orden se muestra."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PostulanteEducacion(_FilaDePerfil):
    __tablename__ = "postulante_educacion"

    postulante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("postulantes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(100), nullable=True)
    institucion: Mapped[str | None] = mapped_column(String(250), nullable=True)
    area_estudio: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nivel_estudio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado_estudio: Mapped[str | None] = mapped_column(String(50), nullable=True)
    inicio_mes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inicio_anio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actualmente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fin_mes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fin_anio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    postulante: Mapped["Postulante"] = relationship(back_populates="educacion")  # noqa: F821


class PostulanteIdioma(_FilaDePerfil):
    __tablename__ = "postulante_idiomas"

    postulante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("postulantes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    idioma: Mapped[str] = mapped_column(String(100), nullable=False)
    nivel_escrito: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nivel_oral: Mapped[str | None] = mapped_column(String(50), nullable=True)

    postulante: Mapped["Postulante"] = relationship(back_populates="idiomas")  # noqa: F821


class PostulanteExperiencia(_FilaDePerfil):
    __tablename__ = "postulante_experiencia"

    postulante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("postulantes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    puesto: Mapped[str | None] = mapped_column(String(250), nullable=True)
    jerarquia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industria: Mapped[str | None] = mapped_column(String(150), nullable=True)
    area_trabajo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    subarea_trabajo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    inicio_mes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inicio_anio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actualmente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fin_mes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fin_anio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    postulante: Mapped["Postulante"] = relationship(back_populates="experiencia")  # noqa: F821
