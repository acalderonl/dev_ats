import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vacante(Base):
    __tablename__ = "vacantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    documento_adjunto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=False, index=True)
    fecha_limite: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    linkedin_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    empleador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), default="activa")
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    cargo: Mapped["Cargo"] = relationship(back_populates="vacantes")  # noqa: F821
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="vacante")  # noqa: F821
