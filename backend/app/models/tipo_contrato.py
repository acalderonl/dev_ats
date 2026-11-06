from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoContrato(Base):
    """Catálogo de tipos de contrato (indefinido, eventual, pasantía...).

    Mismo patrón que los catálogos del cargo: lo sirve el router genérico de
    `/api/v1/catalogos` y se gestiona con el engranaje junto al selector.
    """

    __tablename__ = "tipos_contrato"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vacantes: Mapped[list["Vacante"]] = relationship(back_populates="tipo_contrato")  # noqa: F821
