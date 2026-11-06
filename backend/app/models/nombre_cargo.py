from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NombreCargo(Base):
    """Catálogo de nombres de cargo.

    Existe para que el mismo puesto no se escriba de varias formas distintas
    ("Desarrollador Backend" / "Dev Backend" / "Backend Developer"). Se gestiona
    desde el engranaje que hay junto al selector de nombre en el formulario de cargo.
    """

    __tablename__ = "nombres_cargo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cargos: Mapped[list["Cargo"]] = relationship(back_populates="nombre_catalogo")  # noqa: F821
