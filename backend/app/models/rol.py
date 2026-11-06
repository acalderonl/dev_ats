from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Rol(Base):
    """Un rol agrupa permisos y se asigna a usuarios.

    `es_sistema` marca los tres con los que arranca la aplicación. Están protegidos
    contra renombrado y borrado porque **el código todavía nombra algunos de ellos**
    (`require_roles("super_admin", ...)`): renombrar `reclutador` dejaría a esos
    endpoints sin dejar pasar a nadie, y sin ningún error visible. Los roles que se
    crean desde la pantalla no tienen esa atadura y se pueden cambiar libremente.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")  # noqa: F821
