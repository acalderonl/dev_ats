from datetime import datetime

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Departamento(Base):
    """Unidad organizativa a la que pertenecen los cargos.

    No es lo mismo que la *clasificación* del cargo (Tecnología, Talento Humano...), que
    describe qué tipo de puesto es y sirve para agrupar competencias. El departamento es
    **dónde está** el puesto dentro de la institución: un cargo pertenece a exactamente
    uno, y la pantalla de Cargos se organiza por él.

    `es_sistema` marca el departamento «Sin asignar», que crea la migración para que
    ningún cargo existente quede huérfano. No se puede desactivar ni renombrar: es el
    sitio al que caen los cargos cuando se desactiva su departamento.
    """

    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    cargos: Mapped[list["Cargo"]] = relationship(back_populates="departamento")  # noqa: F821
