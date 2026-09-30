from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cargo(Base):
    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    departamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    preguntas_filtro: Mapped[list["PreguntaFiltro"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan"
    )
    vacantes: Mapped[list["Vacante"]] = relationship(back_populates="cargo")  # noqa: F821
