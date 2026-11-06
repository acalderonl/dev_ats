from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Competencia(Base):
    """Conocimiento académico (`academico`) o habilidad blanda (`blanda`).

    Un solo catálogo para los dos: se gestionan igual y así el buscador de parecidos
    sirve para ambos. `nombre_normalizado` (sin tildes, en minúsculas) es contra lo que se
    compara, para que "Programación" y "programacion" no acaben siendo dos registros.
    """

    __tablename__ = "competencias"
    __table_args__ = (UniqueConstraint("tipo", "nombre_normalizado", name="uq_competencia_tipo_nombre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_normalizado: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cargos: Mapped[list["CargoCompetencia"]] = relationship(back_populates="competencia")  # noqa: F821


class CargoCompetencia(Base):
    """Qué competencia pide un cargo y con qué exigencia."""

    __tablename__ = "cargo_competencias"

    cargo_id: Mapped[int] = mapped_column(Integer, ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True)
    competencia_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competencias.id", ondelete="CASCADE"), primary_key=True
    )
    requerido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deseado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    cargo: Mapped["Cargo"] = relationship(back_populates="competencias")  # noqa: F821
    competencia: Mapped["Competencia"] = relationship(back_populates="cargos")
