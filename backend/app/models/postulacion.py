import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vacantes.id"), nullable=False)
    postulante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("postulantes.id"), nullable=False)
    respuestas_filtro: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    autorizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_autorizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado_pipeline: Mapped[str] = mapped_column(String(50), default="pendiente_autorizacion")
    origen: Mapped[str] = mapped_column(String(20), default="Directo")
    match_score: Mapped[int | None] = mapped_column(Numeric(5, 2), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    vacante: Mapped["Vacante"] = relationship(back_populates="postulaciones")  # noqa: F821
    postulante: Mapped["Postulante"] = relationship(back_populates="postulaciones")  # noqa: F821
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(  # noqa: F821
        back_populates="postulacion", cascade="all, delete-orphan"
    )
