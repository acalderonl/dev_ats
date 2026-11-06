from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ClasificacionCargo(Base):
    """Catálogo de clasificaciones de cargo (ocupa el lugar del antiguo `departamento`)."""

    __tablename__ = "clasificaciones_cargo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cargos: Mapped[list["Cargo"]] = relationship(back_populates="clasificacion_catalogo")  # noqa: F821
