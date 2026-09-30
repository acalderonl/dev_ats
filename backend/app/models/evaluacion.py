import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    postulacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("postulaciones.id", ondelete="CASCADE"), nullable=False
    )
    evaluador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    tipo_evaluacion: Mapped[str] = mapped_column(String(100), nullable=False)
    puntaje: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    postulacion: Mapped["Postulacion"] = relationship(back_populates="evaluaciones")  # noqa: F821
