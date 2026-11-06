import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Postulacion(Base):
    """Una persona postulándose a **una convocatoria** concreta.

    Antes colgaba de la vacante. Desde la migración 0010 cuelga de la convocatoria,
    porque es lo que permite saber a cuál de las rondas se presentó alguien y volver a
    aceptarlo en la siguiente: la misma persona puede postularse a cada convocatoria
    una vez (decisión del dueño el 2026-11-04). Esa regla la aplica el endpoint, no la
    base: la migración encontró datos anteriores que podían tenerla repetida y una
    restricción habría fallado a mitad de camino.
    """

    __tablename__ = "postulaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    convocatoria_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("convocatorias.id"), nullable=False, index=True
    )
    postulante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("postulantes.id"), nullable=False)
    respuestas_filtro: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    autorizado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    fecha_autorizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado_pipeline: Mapped[str] = mapped_column(String(50), default="pendiente_autorizacion")
    origen: Mapped[str] = mapped_column(String(20), default="Directo")
    match_score: Mapped[int | None] = mapped_column(Numeric(5, 2), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    convocatoria: Mapped["Convocatoria"] = relationship(back_populates="postulaciones")  # noqa: F821
    postulante: Mapped["Postulante"] = relationship(back_populates="postulaciones")  # noqa: F821
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(  # noqa: F821
        back_populates="postulacion", cascade="all, delete-orphan"
    )

    @property
    def vacante(self):
        """La vacante, a través de la convocatoria. Lo usan pipeline y contactos."""
        return self.convocatoria.vacante
